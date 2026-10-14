# மலிவு மாமா (Malivu Mama) 🛒

Amazon.in-la 25%+ discount products-ai edukkum. Price history vechu **real discount-ah** nu check pannum. Real-na mattum Telegram-ku anuppum. GitHub Actions-la 24 mani nerum free-aa odum.

## Real discount-ah nu epdi check pannum

Ovvoru product-oda price-um ovvoru run-lum `data/history.json`-la save aagum. Deal anuppa 3 condition-um pass aaganum:

1. MRP-ai vida **25%+ kammi**
2. Kadaisi 30 naal **usual price (median)-ai vida 10%+ kammi** → MRP-ai ethi kaatra fake discount out
3. Kadaisi 30 naal **lowest price kitta** irukkanum

> ⚠️ **Mudhal 7 naal "learning mode"**. History illaama verify panna mudiyaadhu, so andha naal-la deals varaadhu. Daily report mattum varum (9 AM appram). 7 naal kazhichu real deals vara aarambikkum.

## Setup (≈10 nimisham)

### 1. Telegram bot
1. Telegram-la **@BotFather** open panni `/newbot` anuppu. Peru kudu. **Token** copy pannu (`123456:ABC...` maadhiri).
2. Un pudhu bot-ku edhaavadhu oru message anuppu (e.g., `hi`).
3. Browser-la idha open pannu (TOKEN-ai replace pannu):
   `https://api.telegram.org/botTOKEN/getUpdates`
4. Adhula `"chat":{"id":123456789` nu irukkum. Andha number dhaan un **chat ID**.

### 2. GitHub repo
1. github.com-la pudhu repo create pannu. **Private** vechuko.
2. Indha folder-la irukkra ellaa files-um upload pannu (`.github` folder-um sethu; "Add file → Upload files" la drag panna podhum).
   - `.github` hidden folder upload aagalana: repo-la "Add file → Create new file" click panni peru-la `.github/workflows/deals.yml` type pannu, file content-ai paste pannu.
3. Repo **Settings → Secrets and variables → Actions → New repository secret**:
   - `TELEGRAM_BOT_TOKEN` = step 1-la vandha token
   - `TELEGRAM_CHAT_ID` = un chat ID
4. Repo **Settings → Actions → General → Workflow permissions** → **Read and write permissions** select panni Save. (History save aaga idhu venum.)

### 3. Start
**Actions** tab → "Malivu Mama" → **Run workflow**. Green tick vandha work aagudhu. Appram ovvoru mani nerathukkum thaane odum.

## Settings maathanuma?

`config.py` file-la:
- `CATEGORIES` — search keywords add/remove pannu
- `MIN_MRP_DISCOUNT` — 25 → vera %
- `MIN_REAL_DROP` — usual price-ai vida ethana % kammi aaganum
- `SEND_UNVERIFIED = True` — learning mode-lum (verify aagaama) deals venumna

## Theriyanum

- **GitHub free minutes:** private repo-ku maasam 2000 minutes. Ovvoru run 1–2 nimisham, hourly → ~1,000–1,500 minutes. Podhum. Keywords romba add panna `KEYWORDS_PER_RUN` kammi pannu.
- **Amazon block:** GitHub servers-ai Amazon sila neram captcha kaatti block pannum. Bot adha skip panni next run-la try pannum. Daily report-la ethana block aachunu sollum. Romba block aagudhu na sollu, fix pannalam.
- **Amazon page design maaruna** parser udaiyalam ("0 products" nu log-la varum). Appo update pannanum.
- Idhu scraping. Amazon terms-ku against. Personal use-ku mattum, kammiyaana frequency-la vechiruken.
