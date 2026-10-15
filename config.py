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
        "toothpaste", "shampoo", "detergent powder", "face wash",
        "body lotion", "kitchen storage containers", "water bottle steel",
    ],
    "Bags": [
        "laptop backpack", "college bag", "women handbag", "sling bag men",
    ],
    "Watches": [
        "men analog watch", "women analog watch", "men digital watch",
        "couple watch", "kids watch",
    ],
    "Travel": [
        "trolley bag", "duffle bag travel", "travel pouch", "neck pillow travel",
    ],
}

# Ovvoru run-lum ethana keywords check pannanum (GitHub free minutes-ku kammiyaa vechiruken)
KEYWORDS_PER_RUN = 8

# MRP-oda discount ivlo % mela irundha dhaan consider pannum
MIN_MRP_DISCOUNT = 25

# ---- "Real discount ah?" check ----
# Ethana naal price history irundha dhaan verdict sollum
MIN_HISTORY_DAYS = 7
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
HISTORY_KEEP_DAYS = 120
