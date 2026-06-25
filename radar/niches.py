TIER_1_NICHES = [
    "LGBTQ+",
    "Queer-owned brands",
    "Sexual wellness",
    "Dating apps",
    "Fitness",
    "Calisthenics",
    "Strength training",
    "Recovery and wellness apps",
    "Mental wellness",
    "Health tech",
    "SaaS products",
    "Mobile apps",
    "Developer tools",
    "AI products",
    "Black-owned brands",
    "Women-focused brands",
    "Inclusive brands",
]

TIER_2_NICHES = [
    "Lifestyle",
    "Productivity",
    "Travel",
    "Home organization",
    "Home improvement",
    "Outdoor recreation",
    "Hiking",
    "Camping",
    "Sustainable products",
    "Education",
    "Finance apps",
    "Career tools",
    "Food and beverage",
    "Fashion",
    "Beauty",
    "Personal care",
]

TIER_3_NICHES = [
    "Gaming",
    "Board games",
    "Tech accessories",
    "Consumer electronics",
    "Pet products",
    "Subscription boxes",
    "E-commerce brands",
    "Local businesses",
    "Restaurants",
    "Events",
]

OPPORTUNITY_TIER_RULES = """
OPPORTUNITY TIERS:

A (HIGH PRIORITY):
- Explicitly asking for creators / UGC creators / influencers
- Has clear hiring signal
- Has contact method (email, DM, form)
- Immediate outreach opportunity

B (MEDIUM):
- Likely relevant brand or startup
- No explicit hiring signal
- Could be pitched

C (LOW):
- Weak signal or unclear relevance
- Future opportunity only

REJECT:
- Not a brand opportunity
- Discussion posts
- Advice requests
- Job seekers instead of hiring posts
- Spam
"""


def format_niche_tiers_for_prompt() -> str:
    lines = [
        "NICHE TIERS:",
        "",
        "TIER 1 (highest priority):",
        ", ".join(TIER_1_NICHES),
        "",
        "TIER 2:",
        ", ".join(TIER_2_NICHES),
        "",
        "TIER 3:",
        ", ".join(TIER_3_NICHES),
    ]
    return "\n".join(lines)
