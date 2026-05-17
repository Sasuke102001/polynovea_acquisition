# RESEARCH BRIEF: Cuisine-Type Segment Priors for India F&B Venue Intelligence
## Compiled: 2026-05-15 | Geography: Mumbai/MMR (Navi Mumbai, Thane, South Mumbai, Bandra, BKC, Colaba)
## Sources: NRAI IFSR 2024, Swiggy 2024/2025 Insights, Zomato User Insights 2025, Pew Research 2021, Godrej Food Trends 2024, Mordor Intelligence 2025/2026, IMARC Group 2025, Dataintelo 2025, Times of India 2025, Business Standard 2025, Indian Express 2025, Ipsos India 2026, Credence Research 2024, Nuvama Wealth 2023, Equity Edge Research 2025, PMC/IIT Bombay 2022, Restaurant India 2024/2025/2026, Homegrown 2021, SIAL Network 2025

---

## Key Market Baselines (India / Mumbai Context)

| Metric | Value | Source |
|--------|-------|--------|
| India F&B industry (FY24) | ₹5,69,487 Cr (~$68B) | NRAI IFSR 2024 |
| Mumbai organized F&B sector | ₹55,181 Cr | NRAI IFSR 2024 |
| 18–35 age group share of dining-out revenue | 60% | WiFiTalents 2026 |
| Weekend dining share of weekly revenue | 55% | WiFiTalents 2026 |
| Family dining share of casual dining revenue | 45% | WiFiTalents 2026 |
| Average group size in Indian restaurants | 4.2 people | WiFiTalents 2026 |
| North Indian cuisine popularity | 34% of diners nationwide | WiFiTalents 2026 |
| Indians self-identifying as vegetarian | 39% | Pew Research 2021 |
| Jains self-identifying as vegetarian | 92% | Pew Research 2021 |
| Hindus self-identifying as vegetarian | 44% | Pew Research 2021 |
| Indian middle-class proportion (2021) | 31% of population | Equity Edge Research 2025 |
| Gen Z + Millennial QSR visitation | 18% frequent fast-food several times/month | YouGov 2023 |
| Gen Z share of Korean food orders | 27% | Swiggy 2025 / Times of India 2025 |
| Korean food order growth (YoY) | 50% | Swiggy 2025 |
| Pizza market: QSR share | 62% | IMARC Group 2025 |
| Pizza market: non-veg pizza share | 56% | IMARC Group 2025 |
| Sushi: millennial revenue share (global) | 38.6% | Dataintelo 2025 |
| Sushi: luxury tier CAGR | 11.3% | Dataintelo 2025 |
| Barbeque Nation APC (weekend) | ₹1,000–1,300+ tax | Indian Express 2025 |
| Chain casual dining market (FY20) | ₹134 Bn, growing 18% CAGR | Nuvama Wealth 2023 |
| Gen Z tried plant-based foods | 65% | Ipsos India 2026 |
| Gen Z health-conscious self-ID | 78% | Ipsos India 2026 |
| Plant-based food sector growth (2022–2025) | 19% | Ipsos India 2026 |
| Breakfast delivery orders: vegetarian | 90% | Restaurant India 2026 |
| Dine-in share of QSR market | 48.21% | Mordor Intelligence 2026 |
| Delivery CAGR (QSR) | 10.58% | Mordor Intelligence 2026 |
| Asian cuisines share of FSR market | 72.10% | Mordor Intelligence 2026 |
| Zomato monthly transacting users | 24.1M | IRJET / Statista 2025 |
| Swiggy monthly transacting users | 21.6M | IRJET 2025 |
| Zomato market share (food delivery) | 58% | IRJET 2025 |
| Swiggy market share (food delivery) | 42% | IRJET 2025 |
| Average order value (both platforms) | ~₹428 | IRJET 2025 |
| Biryani orders on Swiggy (12 months) | 76 million | Restaurant India 2023 |
| Mumbai biryani-serving restaurants | 22,000+ | Restaurant India 2023 |
| Godrej Food Trends: Korean cuisine gaining mainstream | Yes | Godrej 2024 |
| Godrej Food Trends: ghee resurgence | Yes | Godrej 2024 |

---

## Output A — Narrative Findings by Cuisine Category

---

### REQUEST 1: Indian-Origin Cuisine Types

#### 1. indian_restaurant (generic Indian)
**Who visits in MMR:** The generic Indian restaurant is the most democratic F&B format in Mumbai. It captures the full cross-section of the city — from Udupi-style lunch homes in Matunga to Mughlai joints in Bhendi Bazaar. The "average diner" is a family group (3–5 people) visiting on weekends for a reliable, value-driven meal. Office workers dominate weekday lunch (especially in commercial districts like BKC, Fort, and Nariman Point). Couples use mid-casual Indian for date nights when the budget doesn't stretch to continental. Solo diners are common at counter-service Udupi/Maharashtrian places. College kids treat cheap Indian thali joints as group hangouts. Premium diners avoid generic Indian in favor of regional-specialty or chef-driven Indian fine dining.

**Day-part:** Lunch (weekdays) + Dinner (weekends). All-day for Udupi/Maharashtrian places.
**Party composition:** 3–5 people (families), 1–2 (office workers, solo), 4–6 (college groups).
**Data sources:** NRAI IFSR 2024 (Mumbai F&B size, family dining trends); WiFiTalents 2026 (group size 4.2, weekend dining 55%, family casual dining 45%); Pew Research 2021 (vegetarianism data shapes family composition).

**Sub-type split needed?** YES. The brief already handles this via `north_indian_restaurant`, `south_indian_restaurant`, `vegetarian_restaurant`. Generic Indian should be treated as a fallback when no sub-type is available, with a flatter distribution.

---

#### 2. north_indian_restaurant
**Who visits in MMR:** North Indian is India's most-ordered cuisine (34% nationwide per WiFiTalents). In Mumbai, it functions across three distinct price-band psychographics:
- **Dhaba-style / value** (e.g., roadside Punjabi, Andheri/Goregaon): college kids + office workers + solo diners. Heavy lunch traffic, thali-driven, fast turnover.
- **Family-style / mid-casual** (e.g., Punjab Grill, Pind Balluchi clones, most suburban outlets): families + couples + working women. Weekend dinner dominant. Occasion-driven (birthdays, family get-togethers).
- **Premium / chef-driven** (e.g., Masque, Indian Accent adjacents, ITC Bukhara-style): premium segment + couples + HNW families. Status signaling + culinary experience.

The default Google Places type `north_indian_restaurant` maps most commonly to the mid-casual family format in MMR, because premium North Indian is often tagged as `fine_dining_restaurant` and dhaba-style falls to `fast_food_restaurant` or `indian_restaurant`.

**Day-part:** Dinner (weekends dominant), Lunch (weekdays strong).
**Party composition:** 3–5 (families), 2 (couples), 1–2 (office workers).
**Data sources:** WiFiTalents 2026 (34% popularity, 55% weekend revenue, 45% family casual dining); NRAI IFSR 2024 (experiential dining growth, Mumbai market size); Mordor Intelligence 2026 (dine-in 48% QSR, experiential preference).

---

#### 3. south_indian_restaurant
**Who visits in MMR:** South Indian in Mumbai is heavily breakfast-and-lunch oriented. The Udupi chain culture (Matunga, Chembur, Dadar) creates a unique demographic profile:
- **Office workers** dominate weekday breakfast (idli-vada before commute) and lunch (meals/thali). Speed + value alignment is perfect.
- **Families** visit on weekends for "authentic" breakfast — this is a strong cultural ritual in Mumbai, especially for Maharashtrian and South Indian families.
- **Solo diners** are extremely common — counter seating, fast service, low friction, inconspicuousness.
- **College kids** use cheap South Indian as group hangouts near campus areas (Vidyavihar, Matunga, Dadar).
- **Couples** and **premium** are underrepresented unless the venue is a modern South Indian fine-dining concept (e.g., The Rameshwaram Café, Carnatic-style places in South Mumbai).
- **Working women** are notably present — South Indian restaurants are perceived as safe, clean, well-lit, and family-friendly, making them comfortable for solo women diners.

**Day-part:** Breakfast + Lunch (dominant). Dinner is weaker unless it's a full-service South Indian specialty.
**Party composition:** 1 (solo, office workers), 2–4 (families, college groups), 3–5 (weekend family breakfast).
**Data sources:** Restaurant India 2026 (breakfast dining grew 10%, 90% breakfast delivery orders vegetarian — signals strong morning South Indian demand); WiFiTalents 2026 (group size, weekend patterns); NRAI IFSR 2024 (Mumbai market dynamics).

---

#### 4. vegetarian_restaurant
**Who visits in MMR:** Vegetarian restaurants in Mumbai serve two distinct constituencies:
- **Religious/dietary necessity:** Jain and Hindu (especially Gujarati, Marwari, and some Brahmin communities). 92% of Jains are vegetarian; 44% of Hindus self-identify as vegetarian (Pew Research). These diners visit as **families** (strongest segment) and as **working women** / **solo diners** who need guaranteed meat-free environments.
- **Health/lifestyle choice:** A growing segment of millennials and Gen Z (65% tried plant-based per Ipsos 2026) who are not religiously vegetarian but actively seek vegetarian/vegan options. This group visits as **couples**, **college kids**, and **office workers**.

The "vegetarian restaurant" type in Google Places is often a proxy for Jain-friendly or pure-veg establishments in Mumbai (especially in Ghatkopar, Borivali, Kandivali, Matunga). These are perceived as cleaner, safer, and more family-appropriate than mixed-veg venues.

**Day-part:** Lunch + Dinner (all-day for Gujarati thali places).
**Party composition:** 3–6 (families dominant), 1–2 (solo women, office workers), 2 (couples in health-conscious segment).
**Data sources:** Pew Research 2021 (39% vegetarian nationwide, 92% Jain, 44% Hindu); Ipsos India 2026 (65% Gen Z tried plant-based, 78% health-conscious); Restaurant India 2026 (health-focused meals grew 2.3x).

---

#### 5. vegan_restaurant
**Who visits in MMR:** Vegan is an emerging, niche category in Mumbai. The customer base is:
- **Gen Z / Millennials** (dominant): 65% of Gen Z tried plant-based foods; 78% self-identify as health-conscious. Vegan restaurants are discovery-driven, Instagram-friendly, and experiential.
- **Working women** (strong): safety + health + community alignment. Vegan cafés in Bandra, Khar, and Juhu attract women-centric groups.
- **Couples** (moderate): health-conscious couples use vegan as "conscious dating" — a signal of shared values.
- **Premium** (moderate): vegan is often priced at premium due to ingredient costs and positioning.
- **Families** and **college kids** are weaker — families find vegan too restrictive for multi-generational groups; college kids find it too expensive.
- **Solo diners** (moderate): laptop-friendly vegan cafés with WiFi attract solo remote workers.

**Day-part:** Lunch (weekday) + Brunch (weekend). All-day café format common.
**Party composition:** 2 (couples, friends), 1 (solo remote workers), 3–4 (women's groups).
**Data sources:** Ipsos India 2026 (Gen Z plant-based, health consciousness); Credence Research 2024 (vegan fast food market drivers); News18 2026 (plant-based sector growth 19%, ₹5,500 Cr by 2034); Restaurant India 2026 (Gen Z communal dining 90%, local preference 58%).

---

### REQUEST 2: Western Cuisine Types

#### 6. american_restaurant (sit-down American: ribs, wings, milkshakes — NOT QSR)
**Who visits in MMR:** Sit-down American in Mumbai (Smokin' Joe's style, Johnny Rockets, Hard Rock Cafe adjacents) occupies a narrow niche:
- **College kids** (strong): American casual dining is perceived as "cool," social-media friendly, and group-appropriate. Wings + milkshakes are shareable formats.
- **Couples** (moderate): casual date-night option, especially in mall locations (Phoenix, R-City, Inorbit).
- **Families** (moderate): families with teenage children use American as a compromise cuisine — familiar, non-spicy, kid-friendly.
- **Premium** (weak unless it's a high-end smokehouse): standard American casual is not status-signaling.
- **Office workers** (weak): too heavy/slow for weekday lunch; occasional team lunch outing.

Differentiation from `hamburger_restaurant`: American sit-down has higher check size, table service, and occasion-driven visits. Hamburger joints are grab-and-go or quick-casual.

**Day-part:** Dinner (dominant) + Weekend lunch.
**Party composition:** 3–5 (college groups, families with teens), 2 (couples).
**Data sources:** Restaurant India 2024/2025 (experiential dining trends, social media influence); WiFiTalents 2026 (18–35 drives 60% revenue); NRAI IFSR 2024 (Mumbai organized sector size).

---

#### 7. hamburger_restaurant (QSR-adjacent burger joints)
**Who visits in MMR:** Burger joints in Mumbai (Smaaash, local chains, NOT McDonald's which is `fast_food_restaurant`) target:
- **College kids** (dominant): burgers are the quintessential youth QSR format. Burger King India explicitly targets 18–35 males with student-friendly pricing and digital-first campaigns.
- **Office workers** (moderate): quick lunch, delivery-heavy, low friction.
- **Solo diners** (moderate): single-burger meals are perfect for solo consumption.
- **Families** (weak): unless it's a mall-based outlet with seating, families prefer full-service.
- **Couples** (weak): not a date-night cuisine unless it's a premium burger bar.

Differentiation from `american_restaurant`: Hamburger is QSR-adjacent — faster, cheaper, smaller format, higher delivery share.

**Day-part:** Lunch (weekday) + Late evening (weekend).
**Party composition:** 1 (solo), 2–3 (college friends, office pairs), 4+ (college groups).
**Data sources:** Troodeo 2025 (Burger King India digital-first, 18–35 core, student offers); Business Standard 2025 (QSR Gen Z targeting, Hallyu wave); YouGov 2023 (18% Gen Z/Millennial frequent fast-food); IMARC Group 2025 (QSR pizza/burger dynamics).

---

#### 8. italian_restaurant (full-service pasta/pizza, mid-casual sit-down)
**Who visits in MMR:** Italian full-service in Mumbai (not Domino's) spans a wide range but clusters around:
- **Couples** (strong): Italian is the default "safe" date-night cuisine in Mumbai — romantic positioning, wine availability, familiar menu.
- **Families** (strong): Italian is perceived as kid-friendly (pasta, pizza), making it a top family weekend choice.
- **Premium** (moderate): higher-end Italian (Olive Bar & Kitchen, Celini, CinCin) attracts status-conscious diners and HNW families.
- **Office workers** (moderate): team lunches at mid-casual Italian in BKC/Andheri business districts.
- **College kids** (weak unless it's a budget pasta place): Italian full-service is too expensive for regular college visits.

**Day-part:** Dinner (weekends dominant) + Lunch (weekday office teams).
**Party composition:** 2 (couples), 3–5 (families), 4–8 (office teams).
**Data sources:** Mordor Intelligence 2026 (FSR dine-in 65%, experiential dining); NRAI IFSR 2024 (Mumbai trendsetter market); WiFiTalents 2026 (weekend dining 55%, family casual 45%).

---

#### 9. pizza_restaurant
**Who visits in MMR:** Pizza in India is a **split-category**. The brief correctly flags this. We provide a single blended prior but mark it for sub-type splitting:

**QSR Pizza (Domino's clone, 62% of market per IMARC):**
- Families (strong): weekend home delivery, kid-driven orders.
- College kids (strong): late-night delivery, group orders, price-sensitive.
- Office workers (moderate): team lunch orders, bulk deals.
- Solo diners (moderate): single pizza meals.

**Artisan/Wood-fired Pizza (growing, 22.6% gourmet segment per Dataintelo):**
- Couples (strong): date-night, dine-in, Instagram-worthy.
- Premium (moderate): higher check, ingredient-forward positioning.
- Families (moderate): weekend experiential dining.
- College kids (weak): too expensive for regular visits.

**Blended prior rationale:** In MMR, most Google Places `pizza_restaurant` tags map to QSR-adjacent outlets (local chains, delivery-first). Artisan wood-fired is the minority but growing. The blended prior weights QSR slightly higher.

**Day-part:** Dinner (dominant) + Lunch (weekday). Late night for QSR.
**Party composition:** 3–5 (families, college groups), 2 (couples at artisan), 1 (solo delivery).
**Data sources:** IMARC Group 2025 (62% QSR, 56% non-veg, 48% thick crust, South India 34%); Dataintelo 2025 (gourmet pizza 22.6%, artisan wood-fired growth); SIAL Network 2025 (India pizza market €1B, 9.2% CAGR, local flavors dominant); Restaurant India 2025 (Badshah pizza launch, The Real Pizza Company UK entry).

**Sub-type split needed?** YES. Recommend splitting into `pizza_restaurant_qsr` and `pizza_restaurant_artisan` for scoring accuracy.

---

#### 10. steak_house
**Who visits in MMR:** Steakhouse in Mumbai is culturally constrained — beef is socially/religiously sensitive for large segments (72% of Hindus say someone cannot be Hindu if they eat beef per Pew Research). Mumbai steakhouses therefore:
- Serve **pork, lamb, chicken, and seafood steaks** as substitutes.
- Target **expats, Christians, Muslims, and liberal urban Hindus** — a narrow demographic.
- Position as **premium/exclusive** by necessity (high ingredient cost, niche demand).

**Customer segments:**
- **Premium** (dominant): steakhouse is a status signal — high check, imported cuts, wine pairing.
- **Couples** (strong): special-occasion dining, anniversary/birthday destination.
- **Office workers** (weak): occasional corporate entertaining.
- **Families** (weak): too expensive and culturally narrow for multi-generational groups.
- **College kids** (very weak): price-prohibitive.

**Day-part:** Dinner only. Weekend dominant.
**Party composition:** 2 (couples), 4–6 (corporate groups, expat friend groups).
**Data sources:** Pew Research 2021 (beef taboo data, 72% Hindu beef identity link); NRAI IFSR 2024 (premium dining growth, experiential trend); Mordor Intelligence 2026 (FSR premium segment).

---

#### 11. barbecue_restaurant (American BBQ style)
**Who visits in MMR:** American BBQ is a small but growing category in Mumbai. It maps closely to the Barbeque Nation model (though BBQ Nation is Indian-casual-dining, not American BBQ). True American BBQ joints:
- **College kids** (strong): shareable meats, craft beer adjacencies, social energy.
- **Couples** (moderate): casual date-night, especially in Bandra/Khar hipster zones.
- **Families** (moderate): weekend indulgence, all-you-can-eat formats appeal to Indian family psychology.
- **Premium** (weak unless it's a smokehouse): American BBQ in India is mid-premium, not luxury.
- **Office workers** (moderate): team outings, Friday night gatherings.

**Day-part:** Dinner (dominant) + Weekend lunch.
**Party composition:** 3–5 (college groups, families), 4–8 (office teams), 2 (couples).
**Data sources:** Indian Express 2025 (Barbeque Nation casual dining model, ₹1,000 APC, family/corporate outings); Nuvama Wealth 2023 (chain CDR market ₹134 Bn, 18% CAGR, family involvement); Dataintelo 2025 (BBQ restaurant market, mid-range largest segment, premium growth).

---

### REQUEST 3: Asian Cuisine Types

#### 12. chinese_restaurant (Indochinese vs authentic)
**Who visits in MMR:** Chinese is the second-most-popular cuisine category in India after North Indian (fusion/Indo-Chinese is explicitly the #2 per WiFiTalents). In Mumbai, it bifurcates:

**Indo-Chinese (Hakka noodles, Manchurian, Schezwan):**
- **College kids** (dominant): Indo-Chinese is the default "cool cheap food" for Indian youth. Group hangouts, street-side stalls, budget joints.
- **Families** (strong): weekend lunch/dinner, especially in suburban Mumbai. Reliable, spicy, kid-friendly adaptations.
- **Office workers** (moderate): quick lunch, delivery.
- **Couples** (moderate): casual date-night.
- **Solo diners** (moderate): quick bowls, low friction.

**Authentic Chinese (dim sum, Sichuan, Cantonese):**
- **Premium** (strong): authentic Chinese signals cosmopolitan sophistication — especially in South Mumbai, BKC, and Bandra.
- **Couples** (strong): dim sum brunch is a couple ritual in Mumbai.
- **Families** (moderate): weekend dim sum outings.
- **Office workers** (moderate): business lunch in BKC/South Mumbai.

**Blended prior:** Most `chinese_restaurant` tags in MMR are Indo-Chinese. Authentic Chinese is the minority but higher-value. We weight Indo-Chinese higher.

**Day-part:** Lunch + Dinner (all-day for Indo-Chinese). Dim sum brunch for authentic.
**Party composition:** 3–5 (families, college groups), 2 (couples), 4–8 (office teams at authentic).
**Data sources:** WiFiTalents 2026 (Indo-Chinese #2 popular, 65% prefer spicy); Swiggy 2024 (noodle bowls 4.55 Cr orders, #3 after biryani/pizza); NRAI IFSR 2024; Mordor Intelligence 2026 (Asian cuisines 72.10% of FSR).

**Sub-type split needed?** YES. Recommend `chinese_restaurant_indo` and `chinese_restaurant_authentic` for accuracy.

---

#### 13. japanese_restaurant (sushi / ramen / teppanyaki)
**Who visits in MMR:** Japanese in Mumbai is premium-positioned by default. Even mid-range Japanese is perceived as "upmarket" due to ingredient costs and cuisine unfamiliarity.
- **Premium** (strong): Japanese is a status cuisine in Mumbai — omakase, sake pairings, Taj/ITC-level outlets.
- **Couples** (strong): sushi is a date-night staple for affluent millennials.
- **Office workers** (moderate): business entertaining in BKC/South Mumbai.
- **Families** (weak): too expensive and "adventurous" for most Indian families with young children.
- **College kids** (weak): price-prohibitive unless it's a budget ramen joint.
- **Working women** (moderate): Japanese restaurants are perceived as safe, clean, and sophisticated — attractive for women-centric groups.

**Day-part:** Dinner (dominant) + Weekend lunch (ramen/brunch formats).
**Party composition:** 2 (couples), 4–6 (business groups, friend groups), 1 (solo at ramen counters).
**Data sources:** Restaurant India 2021 (sushi orders up 50% since 2019, Swiggy data; Zomato premium audience); Dataintelo 2025 (sushi market, millennials 38.6%, luxury tier 11.3% CAGR); Mordor Intelligence 2026 (niche Asian growth for younger consumers).

---

#### 14. thai_restaurant
**Who visits in MMR:** Thai in Mumbai occupies a "curious middle-class" niche:
- **Couples** (strong): Thai is perceived as romantic, aromatic, and "different but not scary" — ideal for date nights.
- **Premium** (moderate): higher-end Thai (Thai Pavilion, Mekong) attracts status-conscious diners.
- **Families** (moderate): families with older children or travel-exposed parents.
- **Office workers** (weak): not a common business-lunch cuisine.
- **College kids** (weak): too expensive and unfamiliar for regular visits.
- **Working women** (moderate): Thai cafés in Bandra/Khar attract women for lunch.

**Day-part:** Dinner (dominant) + Weekend lunch.
**Party composition:** 2 (couples), 3–4 (families, women's groups), 4–6 (friend groups).
**Data sources:** Mordor Intelligence 2026 (niche Asian cuisines growing among younger consumers); NRAI IFSR 2024 (experiential dining); Restaurant India 2025 (global flavor experimentation).

---

#### 15. korean_restaurant
**Who visits in MMR:** Korean in Mumbai is driven by the K-wave (K-pop, K-dramas). Swiggy data shows 50% YoY growth in Korean orders, with Gen Z accounting for 27% of all Korean food orders.
- **College kids** (dominant): K-culture fans, group hangouts, BBQ-at-table formats, Soju nights.
- **Couples** (strong): Korean BBQ is a trendy date-night format.
- **Gen Z / Millennials** (strong across segments): this is the most youth-skewed cuisine in the dataset.
- **Families** (weak): too unfamiliar and spicy for most Indian families.
- **Premium** (weak): Korean in Mumbai is mid-premium, not luxury.
- **Office workers** (weak): occasional team outing.

**Day-part:** Dinner (dominant) + Late evening.
**Party composition:** 3–5 (college groups, K-culture fan groups), 2 (couples), 4–8 (office teams).
**Data sources:** Swiggy 2025 / Times of India 2025 (50% YoY growth, Gen Z 27%, emerging cities 59% rise); Godrej Food Trends 2024 (Korean cuisine mainstreaming); Business Standard 2025 (QSR Hallyu wave, Burger King Korean menu).

---

#### 16. sushi_restaurant (standalone)
**Who visits in MMR:** Standalone sushi is even more premium than general Japanese. It signals "serious culinary interest" or "expense account dining."
- **Premium** (dominant): omakase, chef's counter, imported fish — this is the most premium-skewed category in the dataset.
- **Couples** (strong): special-occasion, anniversary, proposal dinners.
- **Office workers** (moderate): high-end business entertaining.
- **Families** (very weak): not a family format.
- **College kids** (very weak): price-prohibitive.
- **Working women** (moderate): women-centric groups at mid-range sushi.

**Day-part:** Dinner only. Weekend dominant.
**Party composition:** 2 (couples), 4–6 (business groups), 1 (solo at sushi bar).
**Data sources:** Restaurant India 2021 (sushi 50% order growth, premium Zomato audience); Dataintelo 2025 (sushi market, luxury tier 26.7%, 11.3% CAGR); Mordor Intelligence 2026 (premium FSR trends).

---

#### 17. ramen_restaurant (standalone)
**Who visits in MMR:** Standalone ramen in Mumbai is niche — it appeals to:
- **College kids** (strong): affordable Japanese, Instagram-worthy, K-culture adjacent.
- **Solo diners** (strong): ramen counter culture is perfect for solo dining — quick, warm, low social pressure.
- **Couples** (moderate): casual date-night, especially in Bandra/Khar.
- **Office workers** (moderate): quick solo lunch in business districts.
- **Premium** (weak): ramen is not status-signaling in Mumbai.
- **Families** (weak): too niche for family outings.

**Day-part:** Lunch + Dinner. Late evening for college areas.
**Party composition:** 1 (solo), 2 (couples), 3–4 (college friends).
**Data sources:** Swiggy 2025 (ramen among most searched Korean/Japanese items); Restaurant India 2021 (sushi/ramen growth); Times of India 2025 (Korean ramen search trends).

---

#### 18. asian_restaurant (generic pan-Asian)
**Who visits in MMR:** Generic Asian (Thai + Chinese + Japanese on one menu) is the "safe choice" for groups with mixed preferences:
- **Families** (strong): pan-Asian solves the "everyone wants something different" problem. Weekend dominant.
- **Office workers** (moderate): team lunches, safe corporate choice.
- **Couples** (moderate): casual date-night when neither wants Indian.
- **College kids** (moderate): group hangouts, especially in mall food courts.
- **Premium** (weak): generic Asian is not premium-positioned.

**Day-part:** Lunch + Dinner.
**Party composition:** 3–6 (families, office teams), 2 (couples), 4–6 (college groups).
**Data sources:** Mordor Intelligence 2026 (Asian cuisines 72.10% of FSR, pan-Asian familiarity); NRAI IFSR 2024 (family dining trends).

---

#### 19. asian_fusion_restaurant (SoHo / urban casual)
**Who visits in MMR:** Asian fusion in Mumbai (Bandra, Khar, Juhu, Lower Parel) is explicitly targeting the "creative class":
- **Couples** (strong): fusion is experiential, Instagram-driven, and signals cultural capital.
- **College kids** (strong): Gen Z's favorite — 73% actively look for new cuisines, 90% enjoy communal formats.
- **Premium** (moderate): higher check than generic Asian, but not fine-dining.
- **Working women** (moderate): safe, trendy, women-friendly spaces.
- **Office workers** (moderate): after-work drinks + small plates in Lower Parel/Bandra.
- **Families** (weak): too experimental for conservative family palates.

**Day-part:** Dinner (dominant) + Weekend brunch.
**Party composition:** 2–4 (couples, friend groups), 3–5 (women's groups), 4–8 (office teams).
**Data sources:** Restaurant India 2026 (Gen Z 73% seek new cuisines, 90% communal, 58% independent restaurants); NRAI IFSR 2024 (Mumbai trendsetter); Godrej Food Trends 2024 (provenance, authenticity trends).

---

#### 20. middle_eastern_restaurant (Lebanese, Persian, Afghani adjacents)
**Who visits in MMR:** Middle Eastern is strong in Bandra/BKC/Colaba — areas with expat and cosmopolitan populations:
- **Couples** (strong): hummus, mezze, and shisha-adjacent ambience create romantic/casual date-night appeal.
- **Premium** (moderate): Lebanese fine-dining (e.g., Souk, Taj properties) attracts status-conscious diners.
- **Office workers** (moderate): business lunch in BKC — Mediterranean/Middle Eastern is perceived as healthy.
- **Families** (moderate): mezze sharing format works for families with older children.
- **College kids** (moderate): shawarma/falafel joints near campuses.
- **Working women** (moderate): perceived as healthy, safe, and sophisticated.

**Day-part:** Dinner (dominant) + Lunch (BKC/Bandra business).
**Party composition:** 2 (couples), 3–5 (families, friend groups), 4–6 (office teams).
**Data sources:** NRAI IFSR 2024 (Mumbai cosmopolitan dining); Mordor Intelligence 2026 (health-conscious trends); Restaurant India 2025 (experiential dining, story-driven).

---

### REQUEST 4: Quick-Service / Protein Types

#### 21. chicken_restaurant (KFC-adjacent, chicken-first positioning)
**Who visits in MMR:** Chicken-first QSR (KFC, local fried chicken chains) is distinct from generic fast food:
- **Families** (strong): chicken is the most accepted meat across Indian demographics (even many vegetarians eat chicken). Family bucket meals are a strong format.
- **College kids** (strong): fried chicken is a youth staple — shareable, indulgent, social-media friendly.
- **Office workers** (moderate): quick lunch, delivery.
- **Solo diners** (moderate): single-combo meals.
- **Couples** (weak): not a date-night format.
- **Premium** (weak): chicken QSR is not status-signaling.

**Day-part:** Lunch + Dinner. Late evening strong for college areas.
**Party composition:** 3–5 (families, college groups), 1 (solo), 2 (college pairs).
**Data sources:** Mordor Intelligence 2026 (QSR chicken segment); WiFiTalents 2026 (18–35 revenue share); Business Standard 2025 (KFC Gen Z targeting, Carry Minati collab).

---

#### 22. chicken_wings_restaurant (sport bar adjacent)
**Who visits in MMR:** Wings joints in Mumbai are explicitly bar/sports-bar adjacent:
- **College kids** (dominant): wings + beer is the quintessential college male hangout format.
- **Couples** (weak): not a date-night format unless both are sports fans.
- **Office workers** (moderate): after-work sports viewing in BKC/Andheri.
- **Families** (very weak): not family-appropriate.
- **Premium** (weak): wings are casual, not premium.

**Day-part:** Evening + Late night. Weekend dominant.
**Party composition:** 3–6 (college friend groups), 4–8 (office teams).
**Data sources:** Restaurant India 2024/2025 (sports bar trends, male-skewed formats); WiFiTalents 2026 (young male dining patterns).

---

#### 23. kebab_shop (seekh, shami, street-adjacent)
**Who visits in MMR:** Kebab shops in Mumbai span street stalls to sit-down:
- **Solo diners** (strong): quick kebab roll, eat-while-walking or stand-and-eat.
- **Office workers** (strong): quick lunch/dinner grab, especially near railway stations and commercial areas.
- **College kids** (strong): cheap, filling, flavorful — perfect for student budgets.
- **Families** (moderate): sit-down kebab shops (especially Mughlai-style) for weekend family meals.
- **Couples** (moderate): casual date-night at mid-range kebab joints.
- **Premium** (weak): kebab is street-food heritage, not luxury (unless it's a fine-dining kebab restaurant tagged differently).

**Day-part:** Lunch + Dinner. Late night strong.
**Party composition:** 1 (solo), 2 (office pairs, couples), 3–5 (families, college groups).
**Data sources:** NRAI IFSR 2024 (street food to organized transition); WiFiTalents 2026 (spicy preference 65%); Restaurant India 2023 (biryani/kebab culture, 76M biryani orders).

---

#### 24. shawarma_restaurant (late night, delivery-heavy)
**Who visits in MMR:** Shawarma in Mumbai is a **late-night, value-driven, delivery-first** category:
- **College kids** (dominant): post-party food, late-night cravings, budget-friendly.
- **Solo diners** (strong): single shawarma roll is the perfect solo meal.
- **Office workers** (moderate): late-shift workers, delivery to office.
- **Couples** (weak): not a date format.
- **Families** (weak): not a family dining format.
- **Premium** (very weak): shawarma is street food, not premium.

**Day-part:** Late evening + Late night (9 PM–2 AM). Delivery dominant.
**Party composition:** 1 (solo), 2–3 (college friends), 1 (delivery solo).
**Data sources:** Restaurant India 2024 (late-night ordering trends); Swiggy 2024 (late-night Mumbai data); WiFiTalents 2026 (young male dining).

---

#### 25. sandwich_shop (Subway-adjacent)
**Who visits in MMR:** Sandwich shops in India occupy a narrow "health-conscious quick lunch" niche:
- **Office workers** (dominant): Subway and clones are explicitly positioned as "healthier than burger" lunch options. BKC, Andheri, Nariman Point strongholds.
- **Working women** (strong): perceived as light, healthy, safe — strong women customer base.
- **Solo diners** (strong): single sandwich meals, eat-at-desk or quick counter.
- **College kids** (moderate): budget-friendly, especially near campuses.
- **Families** (weak): not a family format.
- **Couples** (weak): not a date format.
- **Premium** (weak): sandwich is utilitarian, not status.

**Day-part:** Lunch (weekday dominant). Breakfast weak.
**Party composition:** 1 (solo), 2 (office pairs), 3–4 (college groups).
**Data sources:** Mordor Intelligence 2026 (QSR health trends); Restaurant India 2026 (health-focused meals 2.3x growth); WiFiTalents 2026 (office worker patterns).

---

### REQUEST 5: Seafood

#### 26. seafood_restaurant (Mumbai coastal context)
**Who visits in MMR:** Mumbai's seafood culture is unique — Malvani, Goan, Mangalorean, and Konkani cuisines are deeply embedded:

**South Mumbai / Premium Coastal (e.g., Trishna, Mahesh Lunch Home, Konkani Café):**
- **Premium** (strong): seafood in South Mumbai is a status ritual — fresh catch, high check, wine pairing.
- **Families** (strong): Sunday family seafood lunch is a **deep cultural ritual** for Maharashtrian, Goan, and Mangalorean communities.
- **Couples** (strong): romantic seaside/outdoor seating in Colaba, Worli, Bandra.
- **Office workers** (moderate): business lunch at premium seafood places in Fort/BKC.

**Navi Mumbai / Thane / Mid-Casual Coastal (e.g., local Malvani joints, fish thali places):**
- **Families** (dominant): weekend fish thali is the anchor occasion. 3–6 people, multi-generational.
- **Solo diners** (moderate): quick fish fry + sol kadhi at lunch counters.
- **Office workers** (moderate): weekday lunch thali near industrial/commercial zones.
- **College kids** (weak): too expensive for regular visits unless it's a budget joint.

**Blended prior:** The `seafood_restaurant` type in Google Places maps to both. We weight family + premium higher, with geographic nuance flagged for scoring layer 2 (location-based adjustment).

**Day-part:** Lunch (weekend dominant for families, weekday for office) + Dinner.
**Party composition:** 3–6 (families), 2 (couples), 4–8 (business groups), 1 (solo at thali counters).
**Data sources:** Homegrown 2021 (Mumbai Malvani guide, family thali culture, Bandra/Goregaon/Dadar fish thali spots); NRAI IFSR 2024 (Mumbai coastal cuisine identity); TripAdvisor 2025 (Konkani Café reviews, family dining); Mordor Intelligence 2026 (regional specialty growth).

**Geographic split needed?** YES. Recommend `seafood_restaurant_premium` (South Mumbai) and `seafood_restaurant_casual` (Navi Mumbai/Thane) for location-aware scoring.

---

#### 27. fish_and_chips_restaurant
**Who visits in MMR:** Fish and chips is a **rare, Western-tourist/expat-adjacent** category in Mumbai:
- **Expats / Western tourists** (dominant): this cuisine has almost zero native Indian demand.
- **Premium** (moderate): if it exists, it's in South Mumbai (Colaba, Fort) targeting tourists.
- **Couples** (weak): curious Indian couples might try once for novelty.
- **Families** (very weak): Indian families prefer coastal Indian seafood over British-style fried fish.
- **College kids** (very weak): too expensive and unfamiliar.

**Day-part:** Lunch + Dinner (tourist areas).
**Party composition:** 2 (couples, tourist pairs), 1 (solo tourists).
**Data sources:** INFERRED — no India-specific data found. Based on global tourism patterns and Mumbai expat geography (Colaba, BKC).

---

### REQUEST 6: International / Long-tail Cuisine

For these types, confidence is generally LOW or MED with explicit INFERRED tags where no India data exists.

#### 28. mexican_restaurant
**Who visits in MMR:** Mexican in India is niche, positioned as "fun casual":
- **Couples** (strong): casual date-night, especially in Bandra/Khar.
- **College kids** (strong): tacos, nachos, margaritas — social, shareable, Instagram-friendly.
- **Families** (weak): too spicy/unfamiliar for conservative family palates.
- **Premium** (weak): Mexican is not premium-positioned in Mumbai.
- **Office workers** (moderate): team lunches at mid-casual Mexican in BKC.

**Day-part:** Dinner + Weekend lunch.
**Party composition:** 2 (couples), 3–5 (college groups, office teams).
**Data sources:** INFERRED. Partial data: Restaurant India 2025 (global flavor experimentation); NRAI IFSR 2024 (experiential dining).

---

#### 29. french_restaurant
**Who visits in MMR:** French in Mumbai is ultra-premium and rare:
- **Premium** (dominant): French cuisine is the apex of Western culinary status in India.
- **Couples** (strong): special-occasion, anniversary, proposal.
- **Office workers** (weak): corporate entertaining at 5-star hotel French outlets.
- **Families** (very weak): not a family format.
- **College kids** (very weak): price-prohibitive.

**Day-part:** Dinner only.
**Party composition:** 2 (couples), 4–6 (corporate groups).
**Data sources:** INFERRED. Partial: Mordor Intelligence 2026 (premium FSR trends); NRAI IFSR 2024 (fine dining growth).

---

#### 30. mediterranean_restaurant
**Who visits in MMR:** Mediterranean in Mumbai overlaps with Middle Eastern and health-food positioning:
- **Couples** (strong): healthy, light, romantic — date-night appeal.
- **Working women** (strong): perceived as healthy, safe, sophisticated.
- **Premium** (moderate): higher check than generic, but not fine-dining.
- **Office workers** (moderate): healthy lunch option in BKC/Bandra.
- **Families** (moderate): families with health-conscious parents.

**Day-part:** Lunch + Dinner.
**Party composition:** 2 (couples), 3–4 (women's groups, families), 4–6 (office teams).
**Data sources:** INFERRED. Partial: Mordor Intelligence 2026 (health trends); Restaurant India 2026 (wellness dining).

---

#### 31. lebanese_restaurant
**Who visits in MMR:** Lebanese is stronger than generic Middle Eastern in Mumbai due to hummus/falafel familiarity:
- **Couples** (strong): mezze sharing is romantic, casual.
- **Office workers** (moderate): business lunch in BKC — healthy, light.
- **College kids** (moderate): budget falafel/shawarma joints near campuses.
- **Families** (moderate): sharing format works for families.
- **Working women** (moderate): safe, healthy, women-friendly.

**Day-part:** Lunch + Dinner.
**Party composition:** 2 (couples), 3–5 (families, friend groups), 4–6 (office teams).
**Data sources:** INFERRED. Partial: NRAI IFSR 2024 (Mumbai cosmopolitan dining); Mordor Intelligence 2026 (health-conscious trends).

---

#### 32. turkish_restaurant
**Who visits in MMR:** Turkish in Mumbai is rare — kebab overlaps with Middle Eastern, and baklava/dessert is niche:
- **Couples** (moderate): novelty date-night.
- **Premium** (moderate): Turkish fine-dining is rare but attracts curious affluent diners.
- **College kids** (weak): too unfamiliar.
- **Families** (weak): not a family format.

**Day-part:** Dinner.
**Party composition:** 2 (couples), 4–6 (friend groups).
**Data sources:** INFERRED. No India-specific data found.

---

#### 33. fusion_restaurant
**Who visits in MMR:** Fusion in Mumbai (molecular gastronomy, Indo-Western, chef-driven) is explicitly targeting the experience economy:
- **Couples** (strong): fusion is the ultimate date-night "discovery" cuisine.
- **Premium** (strong): high check, chef reputation, exclusivity.
- **College kids** (moderate): Instagram-driven visits to viral fusion spots.
- **Office workers** (moderate): corporate entertaining at chef-driven fusion.
- **Families** (weak): too experimental for conservative palates.

**Day-part:** Dinner (dominant).
**Party composition:** 2 (couples), 4–6 (corporate groups, friend groups).
**Data sources:** NRAI IFSR 2024 (experiential dining, innovation); Restaurant India 2025 (molecular gastronomy, Farzi Café model); Godrej Food Trends 2024 (provenance + innovation).

---

#### 34. european_restaurant
**Who visits in MMR:** Generic European in Mumbai is typically hotel-based or fine-dining:
- **Premium** (dominant): European is a proxy for "continental fine dining" in India.
- **Couples** (strong): special-occasion dining.
- **Office workers** (moderate): business dining at 5-star European outlets.
- **Families** (weak): not a family format unless it's a hotel buffet.
- **College kids** (very weak): price-prohibitive.

**Day-part:** Dinner (dominant) + Sunday brunch.
**Party composition:** 2 (couples), 4–8 (corporate groups), 3–5 (families at brunch).
**Data sources:** INFERRED. Partial: Mordor Intelligence 2026 (premium FSR); NRAI IFSR 2024 (hotel restaurant trends).

---

## Summary: Sub-Type Splits Recommended

| Cuisine Type | Split Recommended | Rationale |
|--------------|-------------------|-----------|
| `pizza_restaurant` | `pizza_restaurant_qsr` vs `pizza_restaurant_artisan` | 62% QSR vs 22.6% gourmet, completely different demos |
| `chinese_restaurant` | `chinese_restaurant_indo` vs `chinese_restaurant_authentic` | Indo-Chinese = mass youth/family; Authentic = premium/couples |
| `seafood_restaurant` | `seafood_restaurant_premium` (South Mumbai) vs `seafood_restaurant_casual` (Navi Mumbai/Thane) | Cultural ritual vs thali joint; different price bands and demos |

These splits should be handled at the venue-type prior level (Layer 1) or via location-based modifiers (Layer 2), not by over-complicating the cuisine prior.

---

## Confidence Tag Legend
- **HIGH**: Clear India-specific data exists from NRAI, Swiggy/Zomato, EY, IMARC, Mordor, or Pew.
- **MED**: Regional analogy or partial India data + strong behavioral theory alignment.
- **LOW**: Reasoned inference from global patterns, Mumbai F&B context, and cuisine psychology. Marked INFERRED where no India source exists.

---

*Compiled for Polynovea Venue Intelligence System. Baseline → Profile → Strategy → Execute → Measure → Pattern → Decision → Scale.*
