"""Malivu Mama — Amazon.in + AJIO deal bot: 25%+ discount products-ai edukkum, price history vechu
real discount-ah nu check pannum, real-na mattum Telegram-ku anuppum."""

import json
import os
import random
import re
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from bs4 import BeautifulSoup

import config

DATA = Path(__file__).parent / "data"
HISTORY_FILE = DATA / "history.json"
SENT_FILE = DATA / "sent.json"
STATE_FILE = DATA / "state.json"
IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime.now(timezone.utc)
DAY = 86400


# ---------------------------------------------------------------- storage
def load(path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save(path, obj):
    DATA.mkdir(exist_ok=True)
    rows = [f"{json.dumps(k)}:{json.dumps(v, ensure_ascii=False, separators=(',', ':'))}"
            for k, v in obj.items()]
    path.write_text("{\n" + ",\n".join(rows) + "\n}\n")


# ---------------------------------------------------------------- fetching
def make_session():
    from curl_cffi import requests as creq
    s = creq.Session(impersonate="chrome")
    s.headers.update({"Accept-Language": "en-IN,en;q=0.9"})
    return s


def is_blocked(html):
    if 'data-component-type="s-search-result"' in html:
        return False  # real results page
    low = html.lower()
    return ("validatecaptcha" in low or "type the characters you see" in low
            or "api-services-support@amazon.com" in low or len(html) < 5000)


def fetch_search(session, keyword, page=1):
    url = "https://www.amazon.in/s"
    params = {"k": keyword, "page": page}
    for attempt in range(2):
        try:
            r = session.get(url, params=params, timeout=20)
            if r.status_code == 200 and not is_blocked(r.text):
                return r.text
            print(f"  ! blocked/status {r.status_code} for '{keyword}' (try {attempt + 1})")
        except Exception as e:  # network errors
            print(f"  ! error for '{keyword}': {e}")
        time.sleep(random.uniform(10, 20))
    return None


def fetch_ajio(session, keyword):
    params = {"fields": "SITE", "currentPage": 0, "pageSize": 45, "format": "json",
              "query": f"{keyword}:relevance", "sortBy": "relevance", "text": keyword,
              "gridColumns": 3, "advfilter": "true", "platform": "Desktop"}
    headers = {"Accept": "application/json", "Referer": "https://www.ajio.com/"}
    for attempt in range(2):
        try:
            r = session.get("https://www.ajio.com/api/search", params=params,
                            headers=headers, timeout=20)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data.get("products"), list):
                    return data
            print(f"  ! AJIO blocked/status {r.status_code} for '{keyword}' (try {attempt + 1})")
        except Exception as e:
            print(f"  ! AJIO error for '{keyword}': {e}")
        time.sleep(random.uniform(8, 15))
    return None


def parse_ajio(data):
    items = []
    for p in data.get("products") or []:
        if p.get("adsData"):
            continue  # sponsored skip
        code = p.get("code")
        price = (p.get("price") or {}).get("value")
        if not (code and price and p.get("name")):
            continue
        price = round(price)
        mrp = round((p.get("wasPriceData") or {}).get("value") or 0)
        offer = round((p.get("offerPrice") or {}).get("value") or 0)
        brand = (p.get("fnlColorVariantData") or {}).get("brandName") or ""
        imgs = {i.get("format"): i.get("url") for i in p.get("images") or []}
        items.append({
            "asin": f"ajio:{code}",
            "store": "AJIO",
            "url": "https://www.ajio.com" + (p.get("url") or f"/p/{code}"),
            "title": f"{brand} {p['name']}".strip(),
            "price": price,
            "mrp": mrp if mrp > price else None,
            "offer": offer if 0 < offer < price else None,
            "image": imgs.get("product") or next(iter(imgs.values()), None),
            "rating": None,
        })
    return items


# ---------------------------------------------------------------- parsing
def hd_image(url):
    """Search thumbnail (._AC_UL320_.jpg) -> 1000px image (._AC_SL1000_.jpg)."""
    if not url:
        return None
    return re.sub(r"\._[A-Za-z0-9_,.-]+_\.(jpg|jpeg|png|webp)$", r"._AC_SL1000_.\1", url)


def to_price(text):
    if not text:
        return None
    digits = re.sub(r"[^\d.]", "", text)
    try:
        return round(float(digits))
    except ValueError:
        return None


def parse_search(html):
    soup = BeautifulSoup(html, "lxml")
    items = []
    for card in soup.select('div[data-component-type="s-search-result"]'):
        asin = card.get("data-asin")
        if not asin:
            continue
        if card.select_one(".puis-sponsored-label-text, .s-sponsored-label-text"):
            continue  # ads skip
        title_el = card.select_one('[data-cy="title-recipe"]') or card.select_one("h2")
        h2s = [h.get_text(" ", strip=True) for h in card.select("h2")]
        title = " ".join(dict.fromkeys(t for t in h2s if t)) or (title_el and title_el.get_text(" ", strip=True))
        price_el = card.select_one("span.a-price:not(.a-text-price) span.a-offscreen")
        mrp_el = card.select_one("span.a-price.a-text-price span.a-offscreen")
        img_el = card.select_one("img.s-image")
        rating_el = card.select_one("span.a-icon-alt")
        price, mrp = to_price(price_el and price_el.get_text()), to_price(mrp_el and mrp_el.get_text())
        if not (title_el and price and title):
            continue
        items.append({
            "asin": asin,
            "store": "Amazon",
            "url": f"https://www.amazon.in/dp/{asin}",
            "title": title,
            "price": price,
            "mrp": mrp if mrp and mrp > price else None,
            "image": hd_image(img_el.get("src")) if img_el else None,
            "rating": rating_el.get_text(strip=True).split(" ")[0] if rating_el else None,
        })
    return items


# ---------------------------------------------------------------- real-deal check
def record(history, item, category):
    h = history.setdefault(item["asin"], {"points": []})
    h.update(title=item["title"], category=category, image=item["image"])
    ts = int(NOW.timestamp())
    pts = h["points"]
    # orey mani nerathula rendu dhadava paatha, kadaisi value-ai update pannu
    if pts and ts - pts[-1][0] < 3000:
        pts[-1] = [ts, item["price"], item["mrp"]]
    else:
        pts.append([ts, item["price"], item["mrp"]])


def verdict(history, item):
    """Returns (status, info). status: REAL / FAKE / NEW"""
    pts = history.get(item["asin"], {}).get("points", [])
    now = NOW.timestamp()
    past = [p for p in pts if now - p[0] > 3 * 3600]  # ippo eduthadha thavira
    info = {}
    if (not past or (now - past[0][0]) < config.MIN_HISTORY_DAYS * DAY
            or len(past) < config.MIN_POINTS):
        days = (now - past[0][0]) / DAY if past else 0
        return "NEW", {"days": round(days, 1)}

    last30 = [p[1] for p in past if now - p[0] <= 30 * DAY] or [p[1] for p in past]
    usual = statistics.median(last30)
    low30 = min(last30)
    price = item["price"]
    real_drop = (usual - price) / usual * 100
    info = {"usual": round(usual), "low30": low30, "real_drop": round(real_drop),
            "days": round((now - past[0][0]) / DAY)}

    # MRP inflate pannirukkangala? (MRP ethi, price adhe maari)
    mrps = [p[2] for p in past if p[2]]
    info["mrp_inflated"] = bool(item["mrp"] and mrps and item["mrp"] > statistics.median(mrps) * 1.10)

    near_low = price <= low30 * (1 + config.NEAR_LOW_TOLERANCE / 100)
    if real_drop >= config.MIN_REAL_DROP and near_low:
        return "REAL", info
    return "FAKE", info


def should_send(sent, item):
    prev = sent.get(item["asin"])
    if not prev:
        return True
    if item["price"] <= prev["price"] * (1 - config.RESEND_IF_DROPS_MORE / 100):
        return True
    return NOW.timestamp() - prev["ts"] > config.RESEND_AFTER_DAYS * DAY


# ---------------------------------------------------------------- telegram
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


CATEGORY_EMOJI = {"Electronics": "🎧", "Shoes": "👟", "Clothing": "👕", "Daily use": "🧴",
                  "Bags": "🎒", "Watches": "⌚", "Travel": "🧳"}


def build_message(item, category, status, info):
    emoji = CATEGORY_EMOJI.get(category, "🛍️")
    price_line = f"💰 <b>₹{item['price']:,}</b>"
    if item.get("mrp"):
        disc = round((item["mrp"] - item["price"]) / item["mrp"] * 100)
        price_line += f"  <s>₹{item['mrp']:,}</s>  ({disc}% OFF MRP)"
    lines = [f"{emoji} <b>{esc(item['title'][:180])}</b>", price_line]
    if item.get("offer"):
        lines.append(f"🎟️ With coupon: ₹{item['offer']:,}")
    if status == "REAL":
        days = info["days"]
        lines += [
            f"✅ <b>REAL DEAL</b> — {info['real_drop']}% cheaper than the usual price of ₹{info['usual']:,}!",
            f"📉 Lowest Price in 30 Days: ₹{info['low30']:,} ({days} day{'s' if days != 1 else ''} of price history)",
        ]
    else:
        lines.append(f"⏳ Not verified yet — only {info['days']} days of price history")
    if item.get("rating"):
        lines.append(f"⭐ Rating: {item['rating']}/5")
    lines.append(f"🏷️ Category: {category}")
    lines.append(f"🏬 Store: {item.get('store', 'Amazon')}")
    return "\n".join(lines)


def tg(method, payload):
    import urllib.request
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def deal_targets():
    """Deals: un chat + channel (TELEGRAM_CHANNEL_ID secret irundha). Comma pottu pala IDs kudukkalam."""
    ids = []
    for var in ("TELEGRAM_CHAT_ID", "TELEGRAM_CHANNEL_ID"):
        ids += [x.strip() for x in os.environ.get(var, "").split(",") if x.strip()]
    return list(dict.fromkeys(ids))


def send_one(chat, item, text, button):
    try:
        if item.get("image"):
            return tg("sendPhoto", {"chat_id": chat, "photo": item["image"], "caption": text,
                                    "parse_mode": "HTML", "reply_markup": button})
    except Exception:
        pass  # image fail aanaa text-aa anuppu
    return tg("sendMessage", {"chat_id": chat, "text": text, "parse_mode": "HTML",
                              "reply_markup": button, "disable_web_page_preview": True})


def send_deal(item, text):
    store = item.get("store", "Amazon")
    url = item.get("url") or f"https://www.amazon.in/dp/{item['asin']}"
    button = {"inline_keyboard": [[{"text": f"🛒 Shop on {store}", "url": url}]]}
    ok, errors = 0, []
    for chat in deal_targets():
        try:
            send_one(chat, item, text, button)
            ok += 1
        except Exception as e:
            errors.append(f"{chat}: {e}")
    for e in errors:
        print(f"  ! telegram send fail -> {e}")
    if not ok:
        raise RuntimeError("ella chats-kum anuppa mudiyala")


# ---------------------------------------------------------------- daily summary
def maybe_daily_summary(state, history, stats):
    today = NOW.astimezone(IST).date().isoformat()
    hour = NOW.astimezone(IST).hour
    if state.get("summary_day") == today or hour < 9:
        return
    oldest = min((h["points"][0][0] for h in history.values() if h["points"]), default=NOW.timestamp())
    days = (NOW.timestamp() - oldest) / DAY
    ajio = sum(1 for k in history if k.startswith("ajio:"))
    msg = (f"🧓 <b>Malivu Mama — Daily report</b>\n"
           f"Track aagura products: {len(history):,} (Amazon {len(history) - ajio:,}, AJIO {ajio:,})\n"
           f"History: {days:.0f} naal")
    if days < config.MIN_HISTORY_DAYS:
        msg += (f"\n\n⏳ Learning mode — {config.MIN_HISTORY_DAYS} naal history "
                f"serndha apram dhaan real deals verify panni anuppuven.")
    blocked = {k: v for k, v in stats.get("blocked_by", {}).items() if v}
    if blocked:
        parts = ", ".join(f"{k} {v}" for k, v in blocked.items())
        msg += f"\n⚠️ Kadaisi report-la irundhu blocked searches: {parts}"
    me = os.environ["TELEGRAM_CHAT_ID"].split(",")[0].strip()   # daily report unakku mattum
    tg("sendMessage", {"chat_id": me, "text": msg, "parse_mode": "HTML"})
    state["summary_day"] = today


# ---------------------------------------------------------------- main
def main():
    dry = "--dry-run" in sys.argv
    history = load(HISTORY_FILE, {})
    sent = load(SENT_FILE, {})
    state = load(STATE_FILE, {"next": 0})

    session = make_session()
    candidates, stats = {}, {"blocked": 0, "seen": 0, "blocked_by": {}}
    started = time.monotonic()

    stores = [
        ("AJIO", getattr(config, "AJIO_CATEGORIES", {}), getattr(config, "AJIO_KEYWORDS_PER_RUN", 0),
         "next_ajio", lambda kw: (lambda d: parse_ajio(d) if d else None)(fetch_ajio(session, kw))),
        ("Amazon", config.CATEGORIES, config.KEYWORDS_PER_RUN,
         "next", lambda kw: (lambda h: parse_search(h) if h else None)(fetch_search(session, kw))),
    ]
    work = []
    for store, cats, per_run, key, fetch in stores:
        jobs = [(cat, kw) for cat, kws in cats.items() for kw in kws]
        if not jobs or per_run <= 0:
            continue
        start = state.get(key, 0) % len(jobs)
        n = min(per_run, len(jobs))
        state[key] = (start + n) % len(jobs)
        work += [(store, key, jobs, jobs[(start + i) % len(jobs)], fetch) for i in range(n)]

    out_of_time = set()
    for store, key, jobs, (cat, kw), fetch in work:
        if store in out_of_time:
            continue
        if time.monotonic() - started > config.TIME_BUDGET_SEC:
            print(f"  ! time budget over, {store} meedhi next run-la")
            state[key] = jobs.index((cat, kw))
            out_of_time.add(store)
            continue
        print(f"> [{store}] {cat}: {kw}")
        items = fetch(kw)
        if items is None:
            stats["blocked"] += 1
            stats["blocked_by"][store] = stats["blocked_by"].get(store, 0) + 1
            continue
        print(f"  {len(items)} products")
        for it in items:
            stats["seen"] += 1
            record(history, it, cat)
            mrp_off = (it["mrp"] - it["price"]) / it["mrp"] * 100 if it["mrp"] else 0
            if mrp_off >= config.MIN_MRP_DISCOUNT:
                prev = candidates.get(it["asin"])
                candidates[it["asin"]] = (it, prev[1] if prev else cat)  # mudhal category-ai vechukko
        time.sleep(random.uniform(4, 9))

    sent_count = 0
    sent_keys = set()  # orey product-oda size/colour variants-ai orey dhadava anuppa
    for asin, (it, cat) in candidates.items():
        status, info = verdict(history, it)
        print(f"  [{status}] {it.get('store')} ₹{it['price']} / ₹{it['mrp']}  {it['title'][:60]}  {info}")
        if status == "FAKE" or (status == "NEW" and not config.SEND_UNVERIFIED):
            continue
        if not should_send(sent, it) or sent_count >= config.MAX_MESSAGES_PER_RUN:
            continue
        key = (it.get("store"), it["title"].lower()[:80], it["price"])
        if key in sent_keys:
            continue
        text = build_message(it, cat, status, info)
        if dry:
            print("----\n" + text + "\n----")
        else:
            try:
                send_deal(it, text)
            except Exception as e:
                print(f"  ! telegram send fail: {e}")
                continue
            time.sleep(1.5)
        sent[asin] = {"price": it["price"], "ts": int(NOW.timestamp())}
        sent_keys.add(key)
        sent_count += 1

    # pazhaya data clean
    cutoff = NOW.timestamp() - config.HISTORY_KEEP_DAYS * DAY
    for asin in list(history):
        history[asin]["points"] = [p for p in history[asin]["points"] if p[0] >= cutoff]
        if not history[asin]["points"]:
            del history[asin]
    sent = {a: v for a, v in sent.items() if v["ts"] >= cutoff}

    if not dry and os.environ.get("TELEGRAM_BOT_TOKEN"):
        prev = state.get("blocked_today", {})
        if not isinstance(prev, dict):          # pazhaya format (number) -> Amazon
            prev = {"Amazon": prev}
        for k, v in stats["blocked_by"].items():
            prev[k] = prev.get(k, 0) + v
        state["blocked_today"] = prev
        stats["blocked_by"] = prev
        before = state.get("summary_day")
        try:
            maybe_daily_summary(state, history, stats)
        except Exception as e:
            print(f"  ! daily report fail: {e}")
        if state.get("summary_day") != before:
            state["blocked_today"] = {}

    save(HISTORY_FILE, history)
    save(SENT_FILE, sent)
    save(STATE_FILE, state)
    print(f"Done: seen={stats['seen']} candidates={len(candidates)} sent={sent_count} blocked={stats['blocked']}")


if __name__ == "__main__":
    main()
