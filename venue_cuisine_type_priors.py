"""
CUISINE_TYPE_SEGMENT_PRIORS
Drop-in replacement for 012_compute_venue_demographics.py
Geography: Mumbai/MMR (Navi Mumbai, Thane, South Mumbai, Bandra, BKC, Colaba)
Compiled: 2026-05-15
Sources: NRAI IFSR 2024, Swiggy 2024/2025, Zomato 2025, Pew Research 2021, Godrej Food Trends 2024,
         Mordor Intelligence 2025/2026, IMARC Group 2025, Dataintelo 2025, Times of India 2025,
         Business Standard 2025, Indian Express 2025, Ipsos India 2026, Credence Research 2024,
         Nuvama Wealth 2023, Equity Edge Research 2025, PMC/IIT Bombay 2022, Restaurant India 2024-2026,
         Homegrown 2021, SIAL Network 2025, YouGov 2023, WiFiTalents 2026

Confidence: HIGH = clear India data exists
            MED  = regional analogy or partial data + strong behavioral theory
            LOW  = reasoned inference; marked INFERRED where no India source

Tolerance: ±0.01 per cuisine type (all sums verified to 1.00)
"""

from typing import Dict, Tuple

CUISINE_TYPE_SEGMENT_PRIORS: Dict[str, Dict[str, Tuple[float, str, str]]] = {
    # ========================================================================
    # REQUEST 1: Indian-Origin Cuisine Types
    # ========================================================================

    "indian_restaurant": {
        "families":       (0.28, "HIGH", "Family dining contributes 45% of casual dining revenue; average group size 4.2; weekend dining 55% of weekly revenue. Generic Indian is the most democratic format — Udupi to Mughlai. NRAI IFSR 2024; WiFiTalents 2026."),
        "office_workers": (0.22, "HIGH", "Business people rank #1 customer group in Mumbai restaurant surveys; weekday lunch dominant in commercial districts. NRAI IFSR 2024; WiFiTalents 2026."),
        "college_kids":   (0.15, "MED",  "Cheap thali joints and street-adjacent Indian are group hangout staples near campuses. 18-35 drives 60% dining revenue. WiFiTalents 2026; behavioral theory (Cialdini social proof)."),
        "couples":        (0.12, "MED",  "Mid-casual Indian serves as budget date-night when continental is too expensive. Weekend dinner occasion-driven. NRAI IFSR 2024; behavioral theory (Kahneman substitution)."),
        "solo_diners":    (0.10, "HIGH", "Counter-service Udupi/Maharashtrian places are explicitly designed for solo dining — low friction, fast, inconspicuous. NRAI IFSR 2024; Mehrabian-Russell approach-avoidance."),
        "premium":        (0.06, "MED",  "Premium diners avoid generic Indian in favor of chef-driven or regional specialty. Generic Indian captures only the lower end of premium. NRAI IFSR 2024; inferred from fine dining trends."),
        "working_women":  (0.07, "MED",  "Well-lit, family-friendly Indian restaurants are safe and comfortable for solo women diners, especially Udupi and thali formats. Pew Research 2021; behavioral theory (safety-first heuristic)."),
    },

    "north_indian_restaurant": {
        "families":       (0.30, "HIGH", "North Indian is India’s most popular cuisine (34% of diners). Family-style mid-casual is the dominant format in MMR suburbs. Weekend dinner + occasion-driven. WiFiTalents 2026; NRAI IFSR 2024."),
        "office_workers": (0.18, "HIGH", "Dhaba-style and thali joints dominate weekday lunch in commercial districts. Business people = #1 customer group per Mumbai survey. NRAI IFSR 2024."),
        "couples":        (0.16, "MED",  "Mid-casual North Indian (Punjab Grill tier) is a standard date-night choice. Occasion-driven, weekend evenings. NRAI IFSR 2024; behavioral theory (occasion anchoring)."),
        "college_kids":   (0.12, "MED",  "Value dhaba-style North Indian is budget-friendly group food near campuses. 18-35 drives 60% revenue. WiFiTalents 2026."),
        "premium":        (0.10, "MED",  "Premium North Indian (Bukhara-style, chef-driven) attracts HNW families and status diners. NRAI IFSR 2024 (fine dining growth post-COVID)."),
        "solo_diners":    (0.08, "MED",  "Quick thali/counter service attracts solo office workers and commuters. Mehrabian-Russell low-friction preference."),
        "working_women":  (0.06, "MED",  "Family-style North Indian is safe for women but less so than South Indian/Udupi. Moderate presence. Inferred from safety-heuristic literature."),
    },

    "south_indian_restaurant": {
        "office_workers": (0.28, "HIGH", "Breakfast idli-vada and lunch meals are the anchor occasion for office workers in Matunga, Dadar, Chembur. Speed + value alignment perfect. Restaurant India 2026 (breakfast dining +10%); NRAI IFSR 2024."),
        "families":       (0.24, "HIGH", "Weekend family breakfast at Udupi chains is a strong Mumbai cultural ritual, especially Maharashtrian and South Indian families. 90% breakfast delivery orders vegetarian — signals South Indian dominance. Restaurant India 2026; WiFiTalents 2026."),
        "solo_diners":    (0.18, "HIGH", "Counter seating, fast service, low social pressure — South Indian is the most solo-friendly cuisine format in Mumbai. Mehrabian-Russell approach-avoidance; NRAI IFSR 2024."),
        "college_kids":   (0.12, "MED",  "Cheap South Indian near campuses (Vidyavihar, Matunga, Dadar) is group hangout food. Budget-friendly, filling. WiFiTalents 2026."),
        "working_women":  (0.10, "MED",  "Perceived as clean, well-lit, family-friendly — strong safety signal for women. Udupi culture is explicitly welcoming to women. Pew Research 2021; behavioral theory (safety-first)."),
        "couples":        (0.05, "LOW",  "Couples underrepresented unless it is modern South Indian fine dining (Rameshwaram Café tier). Most South Indian is not date-positioned. INFERRED."),
        "premium":        (0.03, "LOW",  "Premium South Indian is rare in MMR unless explicitly fine-dining tagged. Most South Indian is value/mid-casual. INFERRED from market structure."),
    },

    "vegetarian_restaurant": {
        "families":       (0.32, "HIGH", "Jain and Hindu vegetarian families (92% Jain veg, 44% Hindu veg) drive the core demand. Gujarati/Marwari communities in Ghatkopar, Borivali, Matunga. Family thali is the anchor format. Pew Research 2021; NRAI IFSR 2024."),
        "working_women":  (0.18, "HIGH", "Guaranteed meat-free environment is a strong safety/comfort signal for women. Pure-veg restaurants are perceived as cleaner and more family-appropriate. Pew Research 2021; behavioral theory (safety heuristic)."),
        "solo_diners":    (0.14, "MED",  "Solo vegetarians (especially Jain, Hindu religious) seek guaranteed veg environments. Counter thali and quick-service formats. Pew Research 2021; Mehrabian-Russell."),
        "office_workers": (0.12, "MED",  "Vegetarian office workers prefer pure-veg for lunch to avoid cross-contamination concerns. Especially strong in Jain-dominated business communities. Pew Research 2021."),
        "couples":        (0.10, "MED",  "Health-conscious couples (millennial/Gen Z) actively seek vegetarian for lifestyle reasons. 65% Gen Z tried plant-based. Ipsos India 2026."),
        "college_kids":   (0.08, "MED",  "Budget vegetarian is common near campuses, but not as ‘cool’ as Indo-Chinese or burgers. Moderate presence. WiFiTalents 2026."),
        "premium":        (0.06, "MED",  "Premium vegetarian (e.g., Indian Accent veg tasting) attracts HNW health-conscious diners. Growing but still niche. NRAI IFSR 2024; Ipsos India 2026."),
    },

    "vegan_restaurant": {
        "college_kids":   (0.25, "HIGH", "Gen Z drives vegan demand — 65% tried plant-based, 78% health-conscious, 57% influenced by social media. Vegan is discovery-driven and Instagram-friendly. Ipsos India 2026; Restaurant India 2026."),
        "working_women":  (0.20, "HIGH", "Vegan cafés in Bandra/Khar/Juhu attract women-centric groups. Safety + health + community alignment. Ipsos India 2026; behavioral theory (community signaling)."),
        "couples":        (0.18, "MED",  "Health-conscious couples use vegan as ‘conscious dating’ — shared values signal. Growing trend among millennials. Ipsos India 2026; Credence Research 2024."),
        "solo_diners":    (0.15, "MED",  "Laptop-friendly vegan cafés with WiFi attract solo remote workers. All-day format, low pressure. Restaurant India 2026 (co-working café trend)."),
        "premium":        (0.12, "MED",  "Vegan is often priced at premium due to ingredient costs and positioning. Attracts affluent health-conscious diners. Credence Research 2024; Ipsos India 2026."),
        "families":       (0.06, "LOW",  "Families find vegan too restrictive for multi-generational groups. Weak segment unless family is explicitly vegan. INFERRED."),
        "office_workers": (0.04, "LOW",  "Too expensive and niche for regular office lunch. Occasional wellness-driven visit only. INFERRED."),
    },

    # ========================================================================
    # REQUEST 2: Western Cuisine Types
    # ========================================================================

    "american_restaurant": {
        "college_kids":   (0.28, "MED",  "Sit-down American (wings, ribs, milkshakes) is perceived as ‘cool’ and social-media friendly. Group-appropriate, shareable formats. Restaurant India 2024/2025; WiFiTalents 2026."),
        "families":       (0.22, "MED",  "Families with teenage children use American as compromise cuisine — familiar, non-spicy, kid-friendly. Mall locations (Phoenix, R-City) dominant. NRAI IFSR 2024."),
        "couples":        (0.18, "MED",  "Casual date-night in mall locations. American is ‘safe’ and unchallenging for early-stage dating. Behavioral theory (familiarity preference)."),
        "office_workers": (0.14, "MED",  "Occasional team lunch outing. Too heavy/slow for regular weekday lunch. NRAI IFSR 2024."),
        "premium":        (0.08, "LOW",  "Standard American casual is not status-signaling unless it is a high-end smokehouse. Most American in MMR is mid-casual. INFERRED."),
        "solo_diners":    (0.06, "LOW",  "Solo dining possible at mall food courts but not the primary format. INFERRED."),
        "working_women":  (0.04, "LOW",  "Weak segment — American casual is male-skewed in perception (wings, ribs, beer). INFERRED."),
    },

    "hamburger_restaurant": {
        "college_kids":   (0.32, "HIGH", "Burger King India explicitly targets 18-35 males with student pricing, digital campaigns, and Hallyu collabs. Burger is the quintessential youth QSR format. Troodeo 2025; Business Standard 2025; YouGov 2023."),
        "office_workers": (0.20, "HIGH", "Quick lunch, delivery-heavy, low friction. Burger joints are standard office-lunch option in BKC/Andheri. Mordor Intelligence 2026 (QSR delivery growth 10.58% CAGR)."),
        "solo_diners":    (0.18, "MED",  "Single-burger combos are perfect for solo consumption. Counter service, minimal social pressure. Mehrabian-Russell."),
        "families":       (0.14, "MED",  "Mall-based burger joints attract families with young children. Kid-friendly, familiar. NRAI IFSR 2024."),
        "couples":        (0.08, "LOW",  "Not a date-night format unless it is a premium burger bar. Most hamburger restaurants are too casual for couples. INFERRED."),
        "premium":        (0.04, "LOW",  "Hamburger is QSR-adjacent — not premium-positioned. Premium burger bars are rare in MMR. INFERRED."),
        "working_women":  (0.04, "LOW",  "Weak segment — burger joints are perceived as male-skewed, heavy, and less healthy. INFERRED."),
    },

    "italian_restaurant": {
        "couples":        (0.26, "HIGH", "Italian is the default ‘safe’ date-night cuisine in Mumbai — romantic positioning, wine, familiar menu. Strongest couple-skewed cuisine after Japanese. Mordor Intelligence 2026; NRAI IFSR 2024."),
        "families":       (0.24, "HIGH", "Perceived as kid-friendly (pasta, pizza). Top family weekend choice for affluent suburbs. WiFiTalents 2026 (family casual dining 45%); NRAI IFSR 2024."),
        "premium":        (0.16, "MED",  "Higher-end Italian (Olive, Celini, CinCin) attracts status-conscious and HNW families. Fine-dining Italian is a Mumbai staple. Mordor Intelligence 2026."),
        "office_workers": (0.16, "MED",  "Team lunches at mid-casual Italian in BKC/Andheri. Safe corporate choice, broad appeal. NRAI IFSR 2024."),
        "college_kids":   (0.08, "LOW",  "Italian full-service is too expensive for regular college visits unless it is a budget pasta place. INFERRED."),
        "solo_diners":    (0.06, "LOW",  "Possible at counter-service pasta bars but weak at full-service Italian. INFERRED."),
        "working_women":  (0.04, "LOW",  "Moderate — Italian is safe for women but not explicitly women-targeted. INFERRED."),
    },

    "pizza_restaurant": {
        "families":       (0.26, "HIGH", "QSR pizza (62% of market) is weekend home-delivery staple, kid-driven. Family bucket orders dominant. IMARC Group 2025; WiFiTalents 2026."),
        "college_kids":   (0.22, "HIGH", "Late-night delivery, group orders, price-sensitive. Pizza is the #2 ordered cuisine after biryani. Swiggy 2024; IMARC Group 2025."),
        "couples":        (0.16, "MED",  "Artisan/wood-fired pizza (22.6% gourmet segment) is date-night format. QSR pizza is weak for couples. Blended prior weights QSR higher. Dataintelo 2025; SIAL Network 2025."),
        "office_workers": (0.14, "MED",  "Team lunch orders, bulk deals. QSR pizza is standard office food. Mordor Intelligence 2026."),
        "solo_diners":    (0.12, "MED",  "Single pizza meals, especially delivery. Low friction, complete meal. Mehrabian-Russell."),
        "premium":        (0.06, "LOW",  "Artisan wood-fired attracts premium but is minority. Most pizza in MMR is QSR-adjacent. Dataintelo 2025; INFERRED."),
        "working_women":  (0.04, "LOW",  "Weak segment — pizza is not women-targeted unless it is a health-conscious thin-crust format. INFERRED."),
    },

    "steak_house": {
        "premium":        (0.35, "MED",  "Steakhouse is premium by necessity — high ingredient cost, niche demand, imported cuts, wine pairing. Status signal. NRAI IFSR 2024; Mordor Intelligence 2026."),
        "couples":        (0.28, "MED",  "Special-occasion dining — anniversary, birthday, proposal. Romantic positioning. Behavioral theory (occasion anchoring)."),
        "office_workers": (0.14, "LOW",  "Corporate entertaining at premium steakhouses in South Mumbai/BKC. Occasional, high-check. INFERRED."),
        "families":       (0.10, "LOW",  "Too expensive and culturally narrow for multi-generational groups. Beef taboo limits family appeal (72% Hindus link beef-eating to Hindu identity). Pew Research 2021; INFERRED."),
        "college_kids":   (0.08, "LOW",  "Price-prohibitive. Very weak unless it is a budget pork/lamb steak place. INFERRED."),
        "solo_diners":    (0.03, "LOW",  "Extremely rare — steakhouse is social/occasion format. INFERRED."),
        "working_women":  (0.02, "LOW",  "Very weak — steakhouse is male-skewed in perception and not women-targeted. INFERRED."),
    },

    "barbecue_restaurant": {
        "college_kids":   (0.26, "MED",  "Shareable meats, craft beer adjacencies, social energy. American BBQ appeals to youth experimentation. Restaurant India 2024/2025; WiFiTalents 2026."),
        "families":       (0.22, "MED",  "Weekend indulgence — all-you-can-eat formats appeal to Indian family psychology. Barbeque Nation model (though Indian-casual, not American BBQ). Indian Express 2025; Nuvama Wealth 2023."),
        "office_workers": (0.18, "MED",  "Team outings, Friday night gatherings. Social format suits corporate groups. NRAI IFSR 2024."),
        "couples":        (0.16, "MED",  "Casual date-night in Bandra/Khar hipster zones. Craft beer + BBQ pairing. Restaurant India 2025."),
        "premium":        (0.08, "LOW",  "American BBQ in India is mid-premium, not luxury. Premium segment weak. INFERRED."),
        "solo_diners":    (0.06, "LOW",  "Possible at counter-service BBQ but weak at full-service. INFERRED."),
        "working_women":  (0.04, "LOW",  "Weak — BBQ is male-skewed in perception (meat-heavy, beer-centric). INFERRED."),
    },

    # ========================================================================
    # REQUEST 3: Asian Cuisine Types
    # ========================================================================

    "chinese_restaurant": {
        "college_kids":   (0.24, "HIGH", "Indo-Chinese (Hakka, Manchurian, Schezwan) is the default ‘cool cheap food’ for Indian youth. Group hangouts, street stalls, budget joints. WiFiTalents 2026 (Indo-Chinese #2 popular); Swiggy 2024 (noodle bowls 4.55Cr orders)."),
        "families":       (0.22, "HIGH", "Weekend lunch/dinner staple in suburban Mumbai. Reliable, spicy, kid-friendly adaptations. WiFiTalents 2026 (family casual dining 45%); NRAI IFSR 2024."),
        "couples":        (0.16, "MED",  "Casual date-night at Indo-Chinese. Dim sum brunch for authentic Chinese is couple ritual. Restaurant India 2021; Mordor Intelligence 2026."),
        "office_workers": (0.14, "MED",  "Quick lunch, delivery. Business lunch at authentic Chinese in BKC/South Mumbai. NRAI IFSR 2024."),
        "premium":        (0.12, "MED",  "Authentic Chinese (dim sum, Sichuan) signals cosmopolitan sophistication in South Mumbai/BKC. Mordor Intelligence 2026; NRAI IFSR 2024."),
        "solo_diners":    (0.08, "MED",  "Quick bowls, low friction. Especially strong at Indo-Chinese counters. Mehrabian-Russell."),
        "working_women":  (0.04, "LOW",  "Moderate — Chinese is safe but not explicitly women-targeted. INFERRED."),
    },

    "japanese_restaurant": {
        "premium":        (0.28, "HIGH", "Japanese is premium-positioned by default — omakase, sake, Taj/ITC-level. Status cuisine in Mumbai. Restaurant India 2021 (sushi 50% order growth); Dataintelo 2025 (luxury tier 26.7%, 11.3% CAGR)."),
        "couples":        (0.26, "HIGH", "Sushi is a date-night staple for affluent millennials. Romantic, experiential, shareable. Restaurant India 2021; Dataintelo 2025 (millennials 38.6%)."),
        "office_workers": (0.16, "MED",  "Business entertaining in BKC/South Mumbai. Japanese is safe corporate choice for impressing clients. NRAI IFSR 2024."),
        "working_women":  (0.12, "MED",  "Perceived as safe, clean, sophisticated — attractive for women-centric groups. Behavioral theory (safety + status signaling)."),
        "families":       (0.08, "LOW",  "Too expensive and ‘adventurous’ for most Indian families with young children. INFERRED."),
        "college_kids":   (0.06, "LOW",  "Price-prohibitive unless it is a budget ramen joint. Weak at full-service Japanese. INFERRED."),
        "solo_diners":    (0.04, "LOW",  "Possible at sushi bar or ramen counter but weak at full-service. INFERRED."),
    },

    "thai_restaurant": {
        "couples":        (0.30, "MED",  "Thai is perceived as romantic, aromatic, ‘different but not scary’ — ideal date-night. NRAI IFSR 2024; behavioral theory (familiarity + novelty balance)."),
        "premium":        (0.18, "MED",  "Higher-end Thai (Thai Pavilion, Mekong) attracts status-conscious diners. Mordor Intelligence 2026 (niche Asian growth)."),
        "families":       (0.16, "MED",  "Families with older children or travel-exposed parents. Weekend lunch/dinner. NRAI IFSR 2024."),
        "working_women":  (0.14, "MED",  "Thai cafés in Bandra/Khar attract women for lunch. Perceived as healthy, light, safe. Restaurant India 2026."),
        "office_workers": (0.10, "LOW",  "Not a common business-lunch cuisine. Occasional team lunch. INFERRED."),
        "college_kids":   (0.08, "LOW",  "Too expensive and unfamiliar for regular visits. INFERRED."),
        "solo_diners":    (0.04, "LOW",  "Weak — Thai is social/occasion format. INFERRED."),
    },

    "korean_restaurant": {
        "college_kids":   (0.32, "HIGH", "K-wave (K-pop, K-dramas) drives demand. Gen Z = 27% of Korean orders. BBQ-at-table, Soju nights, group hangouts. Swiggy 2025 (50% YoY growth); Times of India 2025; Godrej Food Trends 2024."),
        "couples":        (0.22, "HIGH", "Korean BBQ is a trendy date-night format. Experiential, shareable, Instagram-worthy. Swiggy 2025; Restaurant India 2025."),
        "office_workers": (0.14, "MED",  "Occasional team outing. K-culture is conversation starter. Business Standard 2025 (QSR Hallyu wave)."),
        "families":       (0.12, "LOW",  "Too unfamiliar and spicy for most Indian families. Weak unless family is K-culture exposed. INFERRED."),
        "premium":        (0.10, "LOW",  "Korean in Mumbai is mid-premium, not luxury. Premium segment weak. INFERRED."),
        "solo_diners":    (0.06, "LOW",  "Possible at quick Korean counters but weak at BBQ format. INFERRED."),
        "working_women":  (0.04, "LOW",  "Weak — Korean BBQ is male-skewed in perception (meat-heavy, alcohol-centric). INFERRED."),
    },

    "sushi_restaurant": {
        "premium":        (0.38, "HIGH", "Standalone sushi is the most premium-skewed category. Omakase, chef’s counter, imported fish. Dataintelo 2025 (luxury tier 26.7%, 11.3% CAGR); Restaurant India 2021."),
        "couples":        (0.28, "HIGH", "Special-occasion — anniversary, proposal, celebration. Romantic, exclusive. Behavioral theory (scarcity + status signaling)."),
        "office_workers": (0.16, "MED",  "High-end business entertaining. Sushi = ‘serious culinary interest’ or ‘expense account dining.’ NRAI IFSR 2024."),
        "working_women":  (0.08, "MED",  "Women-centric groups at mid-range sushi. Perceived as sophisticated, safe. Behavioral theory."),
        "families":       (0.04, "LOW",  "Not a family format — too expensive, too niche, raw fish concerns. INFERRED."),
        "college_kids":   (0.04, "LOW",  "Price-prohibitive. Very weak. INFERRED."),
        "solo_diners":    (0.02, "LOW",  "Possible at sushi bar but extremely rare as primary format. INFERRED."),
    },

    "ramen_restaurant": {
        "college_kids":   (0.28, "MED",  "Affordable Japanese, Instagram-worthy, K-culture adjacent. Strong near campuses. Swiggy 2025 (ramen among most searched); Times of India 2025."),
        "solo_diners":    (0.26, "MED",  "Ramen counter culture is perfect for solo dining — quick, warm, low social pressure. Mehrabian-Russell; behavioral theory (comfort food + solitude)."),
        "office_workers": (0.18, "MED",  "Quick solo lunch in business districts. Warm, filling, fast. NRAI IFSR 2024."),
        "couples":        (0.16, "MED",  "Casual date-night in Bandra/Khar. Novelty + affordability. Restaurant India 2025."),
        "premium":        (0.06, "LOW",  "Ramen is not status-signaling in Mumbai. Premium segment very weak. INFERRED."),
        "families":       (0.04, "LOW",  "Too niche for family outings. INFERRED."),
        "working_women":  (0.02, "LOW",  "Weak — ramen is not explicitly women-targeted. INFERRED."),
    },

    "asian_restaurant": {
        "families":       (0.28, "HIGH", "Pan-Asian solves the ‘everyone wants something different’ problem. Strong weekend family choice. Mordor Intelligence 2026 (Asian cuisines 72.10% of FSR); NRAI IFSR 2024."),
        "office_workers": (0.20, "MED",  "Team lunches, safe corporate choice. Broad menu = broad appeal. NRAI IFSR 2024."),
        "couples":        (0.18, "MED",  "Casual date-night when neither wants Indian. Safe, familiar. Behavioral theory (familiarity preference)."),
        "college_kids":   (0.16, "MED",  "Group hangouts in mall food courts. Budget-friendly, variety. WiFiTalents 2026."),
        "premium":        (0.08, "LOW",  "Generic Asian is not premium-positioned. Premium segment weak. INFERRED."),
        "solo_diners":    (0.06, "LOW",  "Possible at food courts but weak at full-service. INFERRED."),
        "working_women":  (0.04, "LOW",  "Moderate — safe but not explicitly women-targeted. INFERRED."),
    },

    "asian_fusion_restaurant": {
        "couples":        (0.26, "MED",  "Fusion is experiential, Instagram-driven, signals cultural capital. Strong date-night appeal. Restaurant India 2026 (Gen Z 73% seek new cuisines); NRAI IFSR 2024."),
        "college_kids":   (0.24, "MED",  "Gen Z favorite — 90% enjoy communal formats, 58% choose independent restaurants. Discovery-driven. Restaurant India 2026."),
        "premium":        (0.16, "MED",  "Higher check than generic Asian, chef-driven. Attracts affluent experimenters. Godrej Food Trends 2024."),
        "working_women":  (0.14, "MED",  "Safe, trendy, women-friendly spaces in Bandra/Khar/Juhu. Restaurant India 2026."),
        "office_workers": (0.12, "MED",  "After-work drinks + small plates in Lower Parel/Bandra. NRAI IFSR 2024."),
        "families":       (0.06, "LOW",  "Too experimental for conservative family palates. Weak. INFERRED."),
        "solo_diners":    (0.02, "LOW",  "Very weak — fusion is social/discovery format. INFERRED."),
    },

    "middle_eastern_restaurant": {
        "couples":        (0.24, "MED",  "Hummus, mezze, shisha-adjacent ambience = romantic/casual date-night. Strong in Bandra/BKC. NRAI IFSR 2024; behavioral theory (sensory ambiance)."),
        "office_workers": (0.18, "MED",  "Business lunch in BKC — Mediterranean/Middle Eastern perceived as healthy, light. Mordor Intelligence 2026 (health trends)."),
        "families":       (0.16, "MED",  "Mezze sharing format works for families with older children. Weekend lunch/dinner. NRAI IFSR 2024."),
        "premium":        (0.14, "MED",  "Lebanese fine-dining (Souk, Taj properties) attracts status-conscious diners. Mordor Intelligence 2026."),
        "working_women":  (0.14, "MED",  "Perceived as healthy, safe, sophisticated. Strong women presence in Bandra/BKC. Restaurant India 2026."),
        "college_kids":   (0.10, "LOW",  "Shawarma/falafel joints near campuses attract budget-conscious students. Weak at full-service. INFERRED."),
        "solo_diners":    (0.04, "LOW",  "Weak at full-service; stronger at quick shawarma counters. INFERRED."),
    },

    # ========================================================================
    # REQUEST 4: Quick-Service / Protein Types
    # ========================================================================

    "chicken_restaurant": {
        "families":       (0.28, "HIGH", "Chicken is the most accepted meat across Indian demographics. Family bucket meals are a strong format. KFC and clones dominate family QSR. Mordor Intelligence 2026; WiFiTalents 2026."),
        "college_kids":   (0.26, "HIGH", "Fried chicken is a youth staple — shareable, indulgent, social-media friendly. Business Standard 2025 (KFC Gen Z targeting)."),
        "office_workers": (0.16, "MED",  "Quick lunch, delivery. Chicken QSR is standard office food. Mordor Intelligence 2026."),
        "solo_diners":    (0.14, "MED",  "Single-combo meals, low friction. Mehrabian-Russell."),
        "couples":        (0.08, "LOW",  "Not a date-night format. Weak. INFERRED."),
        "premium":        (0.04, "LOW",  "Chicken QSR is not premium-positioned. INFERRED."),
        "working_women":  (0.04, "LOW",  "Weak — fried chicken is male-skewed in perception. INFERRED."),
    },

    "chicken_wings_restaurant": {
        "college_kids":   (0.38, "HIGH", "Wings + beer is the quintessential college male hangout. Sports-bar adjacent, social energy. Restaurant India 2024/2025; WiFiTalents 2026."),
        "office_workers": (0.24, "MED",  "After-work sports viewing in BKC/Andheri. Male-skewed team gatherings. NRAI IFSR 2024."),
        "couples":        (0.14, "LOW",  "Weak unless both are sports fans. Not a date format. INFERRED."),
        "families":       (0.10, "LOW",  "Not family-appropriate. Weak. INFERRED."),
        "premium":        (0.06, "LOW",  "Wings are casual, not premium. INFERRED."),
        "solo_diners":    (0.04, "LOW",  "Possible at sports bars but weak as primary format. INFERRED."),
        "working_women":  (0.04, "LOW",  "Very weak — wings + sports bar is male-skewed. INFERRED."),
    },

    "kebab_shop": {
        "solo_diners":    (0.24, "MED",  "Quick kebab roll, eat-while-walking or stand-and-eat. Low friction, high convenience. Mehrabian-Russell."),
        "office_workers": (0.22, "MED",  "Quick lunch/dinner grab near railway stations and commercial areas. NRAI IFSR 2024."),
        "college_kids":   (0.20, "MED",  "Cheap, filling, flavorful — perfect for student budgets. WiFiTalents 2026."),
        "families":       (0.16, "MED",  "Sit-down Mughlai-style kebab shops for weekend family meals. NRAI IFSR 2024."),
        "couples":        (0.10, "LOW",  "Casual date-night at mid-range kebab joints. Weak at street stalls. INFERRED."),
        "premium":        (0.04, "LOW",  "Kebab is street-food heritage, not luxury (unless fine-dining tagged differently). INFERRED."),
        "working_women":  (0.04, "LOW",  "Weak at street-adjacent kebab shops; moderate at sit-down Mughlai. INFERRED."),
    },

    "shawarma_restaurant": {
        "college_kids":   (0.32, "HIGH", "Post-party food, late-night cravings, budget-friendly. Shawarma is the default late-night college food in Mumbai. Restaurant India 2024; Swiggy 2024."),
        "solo_diners":    (0.28, "HIGH", "Single shawarma roll is the perfect solo meal. Delivery-first, low friction. Mehrabian-Russell."),
        "office_workers": (0.18, "MED",  "Late-shift workers, delivery to office. Quick, filling. NRAI IFSR 2024."),
        "couples":        (0.10, "LOW",  "Not a date format. Weak. INFERRED."),
        "families":       (0.06, "LOW",  "Not a family dining format. Weak. INFERRED."),
        "premium":        (0.04, "LOW",  "Shawarma is street food, not premium. INFERRED."),
        "working_women":  (0.02, "LOW",  "Very weak — late-night shawarma is male-skewed in perception. INFERRED."),
    },

    "sandwich_shop": {
        "office_workers": (0.32, "HIGH", "Subway and clones are explicitly positioned as ‘healthier than burger’ lunch options. BKC, Andheri, Nariman Point strongholds. Mordor Intelligence 2026; Restaurant India 2026."),
        "working_women":  (0.24, "HIGH", "Perceived as light, healthy, safe — strong women customer base. Restaurant India 2026 (health-focused meals 2.3x growth)."),
        "solo_diners":    (0.20, "MED",  "Single sandwich meals, eat-at-desk or quick counter. Mehrabian-Russell."),
        "college_kids":   (0.14, "MED",  "Budget-friendly near campuses. WiFiTalents 2026."),
        "families":       (0.04, "LOW",  "Not a family format. Weak. INFERRED."),
        "couples":        (0.04, "LOW",  "Not a date format. Weak. INFERRED."),
        "premium":        (0.02, "LOW",  "Sandwich is utilitarian, not status. INFERRED."),
    },

    # ========================================================================
    # REQUEST 5: Seafood
    # ========================================================================

    "seafood_restaurant": {
        "families":       (0.26, "HIGH", "Weekend family seafood lunch is a deep cultural ritual for Maharashtrian, Goan, Mangalorean communities. Fish thali is the anchor occasion. Homegrown 2021; NRAI IFSR 2024."),
        "premium":        (0.22, "HIGH", "South Mumbai seafood (Trishna, Mahesh Lunch Home) is status ritual — fresh catch, high check, wine. NRAI IFSR 2024; Mordor Intelligence 2026."),
        "couples":        (0.18, "MED",  "Romantic seaside/outdoor seating in Colaba, Worli, Bandra. Special-occasion. Behavioral theory (occasion anchoring)."),
        "office_workers": (0.14, "MED",  "Business lunch at premium seafood in Fort/BKC. Quick fish thali at mid-casual near industrial zones. NRAI IFSR 2024."),
        "solo_diners":    (0.12, "MED",  "Quick fish fry + sol kadhi at lunch counters. Low friction, filling. Mehrabian-Russell."),
        "college_kids":   (0.04, "LOW",  "Too expensive for regular visits unless budget joint. Weak. INFERRED."),
        "working_women":  (0.04, "LOW",  "Moderate at mid-casual thali places; weak at premium. INFERRED."),
    },

    "fish_and_chips_restaurant": {
        "premium":        (0.28, "LOW",  "If it exists, it is in South Mumbai (Colaba, Fort) targeting tourists and expats. Premium positioning by default. INFERRED from global tourism patterns."),
        "couples":        (0.22, "LOW",  "Curious Indian couples might try once for novelty. Weak repeat potential. INFERRED."),
        "families":       (0.16, "LOW",  "Indian families prefer coastal Indian seafood over British-style fried fish. Weak. INFERRED."),
        "solo_diners":    (0.14, "LOW",  "Solo tourists in Colaba/Fort area. Very niche. INFERRED."),
        "office_workers": (0.10, "LOW",  "Occasional expat office workers in BKC. Very weak. INFERRED."),
        "college_kids":   (0.06, "LOW",  "Too expensive and unfamiliar. Very weak. INFERRED."),
        "working_women":  (0.04, "LOW",  "Very weak — not women-targeted. INFERRED."),
    },

    # ========================================================================
    # REQUEST 6: International / Long-tail Cuisine
    # ========================================================================

    "mexican_restaurant": {
        "couples":        (0.28, "LOW",  "Casual date-night in Bandra/Khar. Tacos, nachos, margaritas — social, shareable. INFERRED from global patterns + Mumbai hipster geography."),
        "college_kids":   (0.26, "LOW",  "Tacos and nachos are Instagram-friendly, group-appropriate. Gen Z discovery-driven. INFERRED from Restaurant India 2025 (global flavor experimentation)."),
        "office_workers": (0.16, "LOW",  "Team lunches at mid-casual Mexican in BKC. Occasional. INFERRED."),
        "families":       (0.12, "LOW",  "Too spicy/unfamiliar for conservative family palates. Weak. INFERRED."),
        "premium":        (0.08, "LOW",  "Mexican is not premium-positioned in Mumbai. INFERRED."),
        "solo_diners":    (0.06, "LOW",  "Possible at quick-taco counters but weak at full-service. INFERRED."),
        "working_women":  (0.04, "LOW",  "Weak — Mexican is not explicitly women-targeted. INFERRED."),
    },

    "french_restaurant": {
        "premium":        (0.40, "LOW",  "French is the apex of Western culinary status in India. Ultra-premium, rare. INFERRED from Mordor Intelligence 2026 (premium FSR trends); NRAI IFSR 2024."),
        "couples":        (0.30, "LOW",  "Special-occasion — anniversary, proposal. Romantic, exclusive. INFERRED from global fine-dining patterns."),
        "office_workers": (0.14, "LOW",  "Corporate entertaining at 5-star hotel French outlets. Occasional, high-check. INFERRED."),
        "families":       (0.08, "LOW",  "Not a family format. Weak. INFERRED."),
        "college_kids":   (0.04, "LOW",  "Price-prohibitive. Very weak. INFERRED."),
        "solo_diners":    (0.02, "LOW",  "Extremely rare. INFERRED."),
        "working_women":  (0.02, "LOW",  "Very weak. INFERRED."),
    },

    "mediterranean_restaurant": {
        "couples":        (0.26, "LOW",  "Healthy, light, romantic — date-night appeal. INFERRED from global health trends + Mumbai Bandra/Khar geography."),
        "working_women":  (0.22, "LOW",  "Perceived as healthy, safe, sophisticated. Strong women presence. INFERRED from Mordor Intelligence 2026 (health trends)."),
        "premium":        (0.16, "LOW",  "Higher check than generic, but not fine-dining. INFERRED."),
        "office_workers": (0.16, "LOW",  "Healthy lunch option in BKC/Bandra. INFERRED."),
        "families":       (0.12, "LOW",  "Families with health-conscious parents. Weekend lunch. INFERRED."),
        "college_kids":   (0.04, "LOW",  "Too expensive for regular visits. INFERRED."),
        "solo_diners":    (0.04, "LOW",  "Possible at Mediterranean cafés but weak. INFERRED."),
    },

    "lebanese_restaurant": {
        "couples":        (0.24, "LOW",  "Mezze sharing is romantic, casual. Strong in Bandra/BKC. INFERRED from Middle Eastern dining patterns."),
        "office_workers": (0.20, "LOW",  "Business lunch in BKC — healthy, light. INFERRED."),
        "families":       (0.18, "LOW",  "Sharing format works for families. Weekend lunch. INFERRED."),
        "working_women":  (0.16, "LOW",  "Safe, healthy, women-friendly. INFERRED."),
        "college_kids":   (0.12, "LOW",  "Budget falafel/shawarma joints near campuses. INFERRED."),
        "premium":        (0.06, "LOW",  "Lebanese fine-dining is rare but attracts curious affluent diners. INFERRED."),
        "solo_diners":    (0.04, "LOW",  "Weak at full-service; stronger at quick falafel counters. INFERRED."),
    },

    "turkish_restaurant": {
        "couples":        (0.28, "LOW",  "Novelty date-night. Turkish is rare in Mumbai — curiosity-driven. INFERRED."),
        "premium":        (0.24, "LOW",  "Turkish fine-dining is rare but attracts curious affluent diners. INFERRED."),
        "families":       (0.16, "LOW",  "Not a family format. Weak. INFERRED."),
        "office_workers": (0.14, "LOW",  "Occasional business lunch if near BKC. INFERRED."),
        "college_kids":   (0.10, "LOW",  "Too unfamiliar for regular visits. INFERRED."),
        "solo_diners":    (0.04, "LOW",  "Very weak. INFERRED."),
        "working_women":  (0.04, "LOW",  "Very weak. INFERRED."),
    },

    "fusion_restaurant": {
        "couples":        (0.28, "MED",  "Fusion is the ultimate date-night ‘discovery’ cuisine. Experiential, Instagram-driven. NRAI IFSR 2024; Restaurant India 2025 (molecular gastronomy, Farzi Café model)."),
        "premium":        (0.24, "MED",  "High check, chef reputation, exclusivity. Attracts HNW experimenters. Godrej Food Trends 2024 (provenance + innovation)."),
        "office_workers": (0.18, "MED",  "Corporate entertaining at chef-driven fusion. Impress-client format. NRAI IFSR 2024."),
        "college_kids":   (0.14, "LOW",  "Instagram-driven visits to viral fusion spots. One-time, not repeat. INFERRED from Gen Z behavior."),
        "families":       (0.10, "LOW",  "Too experimental for conservative palates. Weak. INFERRED."),
        "solo_diners":    (0.04, "LOW",  "Very weak — fusion is social/discovery format. INFERRED."),
        "working_women":  (0.02, "LOW",  "Very weak. INFERRED."),
    },

    "european_restaurant": {
        "premium":        (0.34, "LOW",  "Generic European = ‘continental fine dining’ in India. Hotel-based or fine-dining. INFERRED from Mordor Intelligence 2026 (premium FSR); NRAI IFSR 2024."),
        "couples":        (0.26, "LOW",  "Special-occasion dining. Romantic, formal. INFERRED."),
        "office_workers": (0.20, "LOW",  "Business dining at 5-star European outlets. INFERRED."),
        "families":       (0.10, "LOW",  "Not a family format unless hotel buffet. INFERRED."),
        "college_kids":   (0.04, "LOW",  "Price-prohibitive. INFERRED."),
        "solo_diners":    (0.04, "LOW",  "Very weak. INFERRED."),
        "working_women":  (0.02, "LOW",  "Very weak. INFERRED."),
    },
}

# ========================================================================
# VALIDATION: Verify all priors sum to 1.00 (±0.01 tolerance)
# ========================================================================

if __name__ == "__main__":
    errors = []
    for cuisine, segments in CUISINE_TYPE_SEGMENT_PRIORS.items():
        total = sum(v[0] for v in segments.values())
        if abs(total - 1.0) > 0.01:
            errors.append(f"{cuisine}: sums to {total:.4f}")
    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  {e}")
    else:
        print(f"VALIDATION PASSED: All {len(CUISINE_TYPE_SEGMENT_PRIORS)} cuisine types sum to ~1.00")
