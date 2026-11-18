"""Bot settings. Indha file-la mattum maathunaa podhum."""

# Amazon-la search panna vendiya keywords (category: [keywords])
CATEGORIES = {
    "Electronics": [
        "wireless earbuds", "bluetooth headphones", "smartwatch", "power bank",
        "bluetooth speaker", "phone charger fast", "smart tv", "laptop",
        "keyboard mouse combo", "pendrive 64gb",
    ],
    "Shoes": [
        "running shoes men", "sports shoes women", "sneakers men",
        "casual shoes men", "flip flops", "formal shoes men",
    ],
    "Clothing": [
        "men t shirt", "men shirt casual", "women kurta", "men jeans",
        "track pants men", "women top",
    ],
    "Daily use": [
        "toothpaste", "detergent powder", "kitchen storage containers", "water bottle steel",
    ],
    "Skincare & Hair": [
        "shampoo", "conditioner", "hair oil", "hair serum", "face wash",
        "face serum", "moisturizer", "sunscreen spf 50", "body lotion", "lip balm",
    ],
    "Bags": [
        "laptop backpack", "college bag", "sling bag men",
    ],
    "Women Bags": [
        "women handbag", "ladies purse", "women sling bag", "women tote bag",
        "women shoulder bag", "women clutch", "women backpack",
    ],
    "Watches": [
        "men analog watch", "women analog watch", "men digital watch",
        "couple watch", "kids watch",
    ],
    "Travel": [
        "trolley bag", "duffle bag travel", "travel pouch", "neck pillow travel",
    ],
}

# AJIO-la search panna vendiya keywords (AJIO fashion site, adhanaala electronics/daily use illa)
AJIO_CATEGORIES = {
    "Shoes": [
        "men sneakers", "men sports shoes", "women sneakers", "men casual shoes",
        "men formal shoes", "men sandals", "women flats",
    ],
    "Clothing": [
        "men t shirts", "men shirts", "men jeans", "men track pants",
        "women kurtas", "women tops", "women jeans", "men jackets",
    ],
    "Bags": [
        "backpacks", "men sling bags", "laptop bags",
    ],
    "Women Bags": [
        "women handbags", "women sling bags", "women tote bags",
        "women shoulder bags", "women clutches",
    ],
    "Watches": [
        "men watches", "women watches", "smart watches",
    ],
    "Travel": [
        "trolley bags", "duffle bags",
    ],
}

# Ovvoru run-lum ethana keywords check pannanum (GitHub free minutes-ku kammiyaa vechiruken)
KEYWORDS_PER_RUN = 14          # Amazon
AJIO_KEYWORDS_PER_RUN = 8      # AJIO (API fast, oru search-ku 45 products)

# MRP filter (0 = off; real deal-ai history dhaan decide pannum)
MIN_MRP_DISCOUNT = 0

# ---- "Real discount ah?" check ----
# Ethana naal price history irundha dhaan verdict sollum
MIN_HISTORY_DAYS = 7
# Kammiyaa ivlo price points irukkanum (oru point-ai vechu mudivu edukka koodaadhu)
MIN_POINTS = 4
# Usual price (30-day median) vida ivlo % kammi aagirukkanum
MIN_REAL_DROP = 10
# 30-day lowest price-oda ivlo % kulla irukkanum (adhaavadhu "lowest price" nu solla)
NEAR_LOW_TOLERANCE = 2

# History illaadha pudhu products-ai anuppalaama? (False = verified deals mattum)
SEND_UNVERIFIED = False

# Same product-ai thirumba anuppa: price innum ivlo % kuranja, illa ivlo naal kazhichu
RESEND_IF_DROPS_MORE = 5
RESEND_AFTER_DAYS = 7

# Ovvoru run-lum max ethana messages
MAX_MESSAGES_PER_RUN = 15

# Price history ethana naal vechukkanum
HISTORY_KEEP_DAYS = 45

# Ovvoru run-um ivlo seconds-kulla search-ai niruthidum (GitHub job 10 min limit)
TIME_BUDGET_SEC = 330
