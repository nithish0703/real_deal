"""Malivu Mama — Amazon.in deal bot: 25%+ discount products-ai edukkum, price history vechu
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


def build_message(item, category, status, info):
    price_line = f"💰 <b>₹{item['price']:,}</b>"
    if item.get("mrp"):
        disc = round((item["mrp"] - item["price"]) / item["mrp"] * 100)
        price_line += f"   <s>₹{item['mrp']:,}</s>   ({disc}% off MRP)"
    lines = [f"<b>{esc(item['title'][:180])}</b>", "", price_line]
    if status == "REAL":
        lines += [
            f"✅ <b>REAL DEAL</b> — usual price ₹{info['usual']:,}, ippo {info['real_drop']}% kammi",
            f"📉 Idhukku munnaadi 30 naal lowest: ₹{info['low30']:,}  ({info['days']} naal history)",
        ]
    else:
        lines.append(f"⏳ Verify aagala — {info['days']} naal history dhaan irukku")
    if item.get("rating"):
        lines.append(f"⭐ {item['rating']}/5")
    lines.append(f"🏷 {category}")
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


def send_deal(item, text):
    chat = os.environ["TELEGRAM_CHAT_ID"]
    button = {"inline_keyboard": [[{"text": "🛒 Amazon-la paaru",
                                    "url": f"https://www.amazon.in/dp/{item['asin']}"}]]}
    try:
        if item.get("image"):
            tg("sendPhoto", {"chat_id": chat, "photo": item["image"], "caption": text,
                             "parse_mode": "HTML", "reply_markup": button})
        else:
            raise ValueError
    except Exception:
        tg("sendMessage", {"chat_id": chat, "text": text, "parse_mode": "HTML",
                           "reply_markup": button, "disable_web_page_preview": True})


# ---------------------------------------------------------------- daily summary
def maybe_daily_summary(state, history, stats):
    today = NOW.astimezone(IST).date().isoformat()
    hour = NOW.astimezone(IST).hour
    if state.get("summary_day") == today or hour < 9:
        return
    oldest = min((h["points"][0][0] for h in history.values() if h["points"]), default=NOW.timestamp())
    days = (NOW.timestamp() - oldest) / DAY
    msg = (f"🧓 <b>Malivu Mama — Daily report</b>\n"
           f"Track aagura products: {len(history):,}\n"
           f"History: {days:.0f} naal")
    if days < config.MIN_HISTORY_DAYS:
        msg += (f"\n\n⏳ Learning mode — {config.MIN_HISTORY_DAYS} naal history "
                f"serndha apram dhaan real deals verify panni anuppuven.")
    if stats["blocked"]:
        msg += f"\n⚠️ Kadaisi report-la irundhu {stats['blocked']} searches Amazon block pannuchu."
    tg("sendMessage", {"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": msg, "parse_mode": "HTML"})
    state["summary_day"] = today


# ---------------------------------------------------------------- main
def main():
    dry = "--dry-run" in sys.argv
    history = load(HISTORY_FILE, {})
    sent = load(SENT_FILE, {})
    state = load(STATE_FILE, {"next": 0})

    jobs = [(cat, kw) for cat, kws in config.CATEGORIES.items() for kw in kws]
    start = state.get("next", 0) % len(jobs)
    batch = [jobs[(start + i) % len(jobs)] for i in range(min(config.KEYWORDS_PER_RUN, len(jobs)))]
    state["next"] = (start + len(batch)) % len(jobs)

    session = make_session()
    candidates, stats = {}, {"blocked": 0, "seen": 0}
    started = time.monotonic()
    for cat, kw in batch:
        if time.monotonic() - started > config.TIME_BUDGET_SEC:
            print("  ! time budget over, meedhi next run-la")
            state["next"] = jobs.index((cat, kw))
            break
        print(f"> {cat}: {kw}")
        html = fetch_search(session, kw)
        if not html:
            stats["blocked"] += 1
            continue
        items = parse_search(html)
        print(f"  {len(items)} products")
        for it in items:
            stats["seen"] += 1
            record(history, it, cat)
            mrp_off = (it["mrp"] - it["price"]) / it["mrp"] * 100 if it["mrp"] else 0
            if mrp_off >= config.MIN_MRP_DISCOUNT:
                candidates[it["asin"]] = (it, cat)
        time.sleep(random.uniform(4, 9))

    sent_count = 0
    sent_keys = set()  # orey product-oda size/colour variants-ai orey dhadava anuppa
    for asin, (it, cat) in candidates.items():
        status, info = verdict(history, it)
        print(f"  [{status}] ₹{it['price']} / ₹{it['mrp']}  {it['title'][:60]}  {info}")
        if status == "FAKE" or (status == "NEW" and not config.SEND_UNVERIFIED):
            continue
        if not should_send(sent, it) or sent_count >= config.MAX_MESSAGES_PER_RUN:
            continue
        key = (it["title"].lower()[:80], it["price"])
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
        state["blocked_today"] = state.get("blocked_today", 0) + stats["blocked"]
        stats["blocked"] = state["blocked_today"]
        before = state.get("summary_day")
        try:
            maybe_daily_summary(state, history, stats)
        except Exception as e:
            print(f"  ! daily report fail: {e}")
        if state.get("summary_day") != before:
            state["blocked_today"] = 0

    save(HISTORY_FILE, history)
    save(SENT_FILE, sent)
    save(STATE_FILE, state)
    print(f"Done: seen={stats['seen']} candidates={len(candidates)} sent={sent_count} blocked={stats['blocked']}")


if __name__ == "__main__":
    main()
