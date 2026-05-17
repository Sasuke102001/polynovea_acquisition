<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# I need current, India-specific market intelligence for the F\&B / restaurant industry with Mumbai/MMR as the primary context. This is for a venue intelligence system — I need numbers, not general statements. Cite every figure with source and year.

PLATFORM BEHAVIOR — per consumer segment:
For each platform (Zomato, Swiggy Dineout, Google Maps, Google Reviews, Instagram, WhatsApp, Word of Mouth), and for each of the following customer types — office workers, college students, couples, families, premium diners, solo diners, working women — answer:
Is this platform primarily used for discovery, validation, booking, or post-visit review?
Is usage primary, secondary, or marginal for that segment?
Sources to check: Zomato annual reports, Swiggy investor reports, MagicPin India data, NRAI (National Restaurant Association of India) surveys, Redseer or Bain India F\&B reports, Nielsen India consumer studies.
REVPASH BENCHMARKS (Revenue Per Available Seat Hour, in INR):
What is the typical RevPASH range for casual dining restaurants in Mumbai?
For bars and pubs (Mumbai)?
For fine dining (Mumbai)?
How does RevPASH vary by day part (lunch vs dinner vs late night)?
Any published benchmarks from NRAI, Hospitality India, or F\&B consultancies (Technopak, Deloitte India)?
CHANNEL PERFORMANCE BENCHMARKS — India-specific:
For each marketing channel, I need open/engagement rates, ROI multipliers, and repeat visit lift data specific to Indian restaurants or F\&B:
WhatsApp Broadcast — open rate, click rate, repeat visit conversion. Any TRAI or platform-published data?
SMS — open rate in India (current, post-TRAI DND). Is 98% still cited? What's the realistic F\&B response rate?
Instagram Organic — average reach, engagement rate for Mumbai F\&B accounts. Reels vs static posts.
Meta / Instagram Ads — CPM, CPC, and ROAS benchmarks for restaurant ads in India
Google Ads — search intent conversion rate for "restaurant near me" queries in India
Zomato / Swiggy promotions — what ROI do promoted listings deliver? Any published data from Zomato for Business?
Micro-influencers — what follower range qualifies as micro in Indian F\&B? What's the typical cost and ROI per post for a Mumbai food influencer? Is the "6.5x ROI" figure cited anywhere credible?
YouTube Shorts — engagement vs Reels for food content in India
WOM AND REPEAT VISIT DATA — India-specific:
What is the average word-of-mouth referral rate for Indian restaurant diners? (i.e. how many people does a satisfied customer tell?)
Any India-specific NPS or referral data for F\&B?
What is the average repeat visit rate for Indian casual dining? How does it differ by city tier?
Any data on loyalty program effectiveness in Indian restaurants?
DWELL TIME AND SPEND — Indian restaurant benchmarks:
Published average dwell times by dining occasion (weekday lunch, weekend dinner, bar night) in Indian urban restaurants
Average check size by segment type in Mumbai (casual dining vs premium vs bar)
What % of the average Indian restaurant check is alcohol, food, dessert?
Any data on dessert attach rates in Indian F\&B?
SEGMENT-SPECIFIC MARKET DATA:
Working women dining out: is there any published data on frequency, platform preference, or spend patterns for professional women in Indian cities?
Solo dining: is solo dining growing in India? Any MagicPin, Zomato, or NRAI data on solo diner frequency?
Premium dining: how large is the premium casual and fine dining market in Mumbai? Growth rate?
College/youth segment: what does the data say about 18–25 urban Indian dining frequency and spend?
Prioritize data from 2022–2025. For anything older, flag it. For anything extrapolated from non-Indian markets, flag it clearly. I need numbers I can put in a database and defend.

Most of the ultra‑granular, India/Mumbai‑specific metrics you’re asking for (e.g., “RevPASH for Mumbai bars”, “Google Ads conversion rate for ‘restaurant near me’ in India”) are simply not publicly benchmarked; where hard numbers exist I’ve pulled them, and where they don’t I’m giving clearly labelled operational benchmarks or proxies (India‑wide restaurant SaaS, global or cross‑category) so you can decide what to ingest into your model and what to treat as assumptions.[^1][^2][^3]

Below I’ve organized everything into sections matching your brief and flagged each item as: INDIA DATA, INDIA BENCHMARK (operator/consultant heuristic), GLOBAL/GENERIC, or NO DATA.

***

## Data context for India \& Mumbai

- NRAI IFSR 2024 (Technopak summary) reports that average eating‑out frequency in India rose from 6.6 times per month in 2018–19 to 7.9 in 2023–24; within this, consumers dine out 3.7 times and order in 4.2 times per person per month.[^3]
- A media summary of the same NRAI report notes that Mumbaikars consume non‑home‑cooked food 7.92 times per month on average and spend about ₹877 per restaurant visit per capita.[^2]
- NRAI IFSR 2024 values India’s food‑services sector at about ₹5.7 lakh crore in 2024, projected to ₹7.76 lakh crore by 2028 (8.1 percent CAGR), making it a top‑3 global market; this is the backdrop for all India‑level benchmarks below.[^4][^5]

These are population‑level statistics (INDIA DATA) you can safely treat as ground truth for 2023–24.

***

## Platform behavior by segment (discovery / validation / booking / review)

There is **no published quantitative split** like “X percent of Mumbai office workers discover restaurants via Instagram vs Zomato”. Public sources only tell us relative importance and use‑cases by broad segment (e.g., “young ‘Taste Voyagers’ using social media heavily”).[^6][^7][^8][^4]

Below is a **defensible ordinal matrix (3 = primary, 2 = secondary, 1 = marginal, 0 = negligible)** based on India‑specific evidence about how different cohorts use platforms (NRAI IFSR segment descriptions, RestaurantIndia articles, aggregator narratives) — this is **expert classification, not measured shares**, so store it separately from hard metrics.[^8][^9][^6]

### Legend

- Role: D = discovery, V = validation, B = booking, R = review/post‑visit sharing.
- Usage score: 3 = primary, 2 = secondary, 1 = marginal, 0 = negligible.


### Office workers (urban, Mumbai‑type)

| Platform | Role (D/V/B/R) | Usage score | Evidence basis |
| :-- | :-- | :-- | :-- |
| Zomato | D, V, R | 3 | Zomato positions core app as search, ratings and reviews for dining out; NRAI notes high urban app penetration for ordering/dining out.[^10][^4] |
| Swiggy Dineout | B, D, V | 2 | Swiggy says Dineout helped 22 million diners save ₹533 crore with reservations and offers in 2024; bookings skew to urban working professionals.[^11][^12] |
| Google Maps | D, V | 2 | Common “near me” usage for office‑area lunches; no India‑segment stats but widely reported urban discovery behavior.[^7] |
| Google Reviews | V | 2 | Used alongside Maps/Zomato for rating sanity check; NRAI describes social/digital validation for “Taste Voyagers”.[^8] |
| Instagram | D, R | 2 | RestaurantIndia describes “Instagram‑first food brands” and urban professionals influenced by visual feeds.[^6] |
| WhatsApp | R, V | 1–2 | Used for sharing links/offers and small‑group recommendations; WhatsApp has >400M Indian users and is used by restaurant chains for menus and offers.[^13] |
| Word of Mouth | D, V | 3 | RestaurantIndia and Nielsen note word‑of‑mouth as the strongest restaurant marketing lever in India.[^9][^14] |

### College students (18–25, urban)

Evidence: NRAI “Taste Voyagers” skew young and heavy on social sharing; older NRAI/RestaurantIndia work on “aspiring adolescents” shows high weekly eating‑out frequency with strong influence from peers and social media.[^15][^8]


| Platform | Role | Usage score | Notes |
| :-- | :-- | :-- | :-- |
| Zomato | D, V, R | 3 | Default app for price filtering, ratings, photos.[^10] |
| Swiggy Dineout | B, D | 2 | Used when offers/discounts are attractive (student price sensitivity).[^11] |
| Google Maps | D | 2 | Especially for campus‑adjacent localities. |
| Google Reviews | V | 2 | Quick rating check before committing. |
| Instagram | D, R | 3 | Visual discovery primary (“Instagram‑first food brands”, youth posting food content).[^6][^8] |
| WhatsApp | R | 2 | Groups coordinate plans and share venue suggestions.[^13] |
| Word of Mouth | D | 3 | Peer recommendations central; RestaurantIndia and Nielsen emphasize social group influence.[^14][^9] |

### Couples (dating / social)

| Platform | Role | Usage score | Notes |
| :-- | :-- | :-- | :-- |
| Zomato | D, V, R | 3 | Go‑to for “date‑friendly” filters, photos, ratings.[^10] |
| Swiggy Dineout | B | 2–3 | Swiggy reports 2.35 million “just the two of us” reservations nationally, indicating strong use by couples.[^11] |
| Google Maps | D, V | 2 | Especially for unfamiliar localities. |
| Google Reviews | V | 2 | Cross‑checks ambiance/service comments. |
| Instagram | D, R | 3 | Heavy visual discovery; emphasis on ambience/“Instagram‑worthy” places.[^6] |
| WhatsApp | B (direct contact), R | 1–2 | Used to coordinate bookings/offers; some restaurants take WhatsApp reservations.[^13] |
| Word of Mouth | D | 2–3 | Recommendations from friends/colleagues. |

### Families

| Platform | Role | Usage score | Notes |
| :-- | :-- | :-- | :-- |
| Zomato | D, V | 3 | Filters for family‑friendly, veg, kid‑friendly; widely used in metros.[^10][^4] |
| Swiggy Dineout | B | 2 | Offers and table booking for weekend meals.[^11] |
| Google Maps | D | 2 | Used for distance/parking info for kids/older adults. |
| Google Reviews | V | 2 | Service/cleanliness reviews. |
| Instagram | D | 1–2 | Some use for discovery of kid‑friendly buffets, etc. |
| WhatsApp | R | 1–2 | Family groups share suggestions and photos.[^13] |
| Word of Mouth | D | 3 | Strong offline network via relatives/neighbors; RestaurantIndia stresses WOM as key marketing channel.[^9] |

### Premium diners (fine/premium casual)

Evidence: NRAI describes affluent “Taste Voyagers” as heavy social media users who share experiences on platforms like Facebook, Twitter, WhatsApp; restaurant trade articles highlight Instagram for premium concepts.[^6][^8]


| Platform | Role | Usage score | Notes |
| :-- | :-- | :-- | :-- |
| Zomato | D, V, R | 3 | Even premium diners rely on ratings/photos and for discovery of chef‑driven venues.[^10] |
| Swiggy Dineout | B | 2 | Used for premium dining festivals and discount events.[^11] |
| Google Maps | D, V | 2 | Especially for new/locality‑unknown fine dining. |
| Google Reviews | V | 2 | Detailed service/experience comments. |
| Instagram | D, R | 3 | Primary for trend spotting (chef profiles, new venues) and sharing.[^6][^8] |
| WhatsApp | R | 2 | High‑trust micro‑WOM in closed groups; sometimes for direct reservation with hotels.[^13] |
| Word of Mouth | D | 3 | Peer and concierge recommendations very important. |

### Solo diners

RestaurantIndia reports that **solo dining is increasingly common in India’s social dining culture**, though without quantified shares; this trend is concentrated in metros and among younger working adults.[^9]


| Platform | Role | Usage score | Notes |
| :-- | :-- | :-- | :-- |
| Zomato | D, V | 3 | For “quick bite near me”, safety and ambience checks. |
| Swiggy Dineout | B | 1–2 | When reservations are needed (popular brunch, buffets). |
| Google Maps | D | 3 | Very common for solo exploration and location convenience. |
| Google Reviews | V, R | 2–3 | Solo diners often leave detailed reviews.[^9] |
| Instagram | D | 2 | For cafés, brunch spots, co‑working friendly places. |
| WhatsApp | R | 1 | Less critical than for groups. |
| Word of Mouth | D | 2 | Colleague recommendations. |

### Working women (professional)

No India‑wide numeric data by channel, but multiple trade articles highlight rising female workforce participation and independent socializing in metros. Behavior is similar to a blend of office workers and premium diners:[^16]


| Platform | Role | Usage score | Notes |
| :-- | :-- | :-- | :-- |
| Zomato | D, V | 3 | Lunch near office, safe/comfortable venues. |
| Swiggy Dineout | B | 2 | After‑work dinners, brunches. |
| Google Maps | D | 2–3 | Safety/location check. |
| Google Reviews | V | 2–3 | Service, safety, crowd type. |
| Instagram | D, R | 3 | Lifestyle‑driven discovery. |
| WhatsApp | R | 2–3 | Close‑circle WOM and plan coordination.[^13] |
| Word of Mouth | D | 3 | Colleague all‑female networks often drive venue choice. |

**Use case in your system:** treat this matrix as a **qualitative channel‑role encoding**, not as a measured probability. You can store the role (D/V/B/R) as categorical and the intensity (0–3) as an ordinal “channel salience” field, with stronger, numeric metrics coming from your own data once you instrument venue behavior.

***

## RevPASH benchmarks (India, with Mumbai caveats)

There are **no Mumbai‑only RevPASH datasets** published by NRAI, Technopak, or hospitality consultancies; published benchmarks are either global or India‑wide operator heuristics.[^17][^18]

The only explicitly **India‑specific RevPASH ranges** I could find are from Restrofi’s “Restaurant Analytics Metrics to Track — India 2025” blog (Indian SaaS product, referencing Indian casual restaurants).[^1]

### India RevPASH ranges (INDIA BENCHMARK – operator heuristic)

Source: Restrofi, “Restaurant Analytics Metrics to Track — India 2025”.[^1]


| Segment (India) | RevPASH range (₹ per seat‑hour) | Notes |
| :-- | :-- | :-- |
| Casual dine‑in restaurant | ₹80–150 | Positioned as “reasonable target” for Indian casual dine‑in.[^1] |
| Fine dining (India) | ₹200–400 | Benchmark for higher‑priced concepts.[^1] |
| QSR / fast‑casual | Lower RevPASH, compensated by volume (no concrete numbers given).[^1] |  |

These are **not survey medians**; they are practice benchmarks used by an India‑focused analytics vendor (still useful as target bands).

### Global RevPASH benchmarks (GLOBAL/GENERIC – fallback)

Several global sources describe typical RevPASH by concept in USD; these can be used as a directional sanity check but **should be clearly flagged as non‑India**:

- RestaurantBookingSystem article: typical RevPASH benchmarks of about 8–15 USD for casual dining and 18–30 USD for fine dining per seat‑hour (global sample).[^18]
- Similar ranges are echoed by other global hospitality sources, e.g., SiteMinder and Lavu, at 8–15 USD for casual and 15–30 USD for fine dining.[^19][^17]

Converted roughly at India urban price levels, Restrofi’s ₹80–150 casual and ₹200–400 fine dining bands sit below these global dollar ranges, which is consistent with lower menu prices in India relative to US/EU.[^18][^1]

### Daypart variation

No India‑specific RevPASH by daypart data exists. Global RevPASH literature consistently finds:

- Dinner RevPASH noticeably higher than lunch, reflecting both higher occupancy and higher average checks.[^19][^18]
- Example from Lavu (non‑India): lunch RevPASH 19.04 USD vs dinner 25 USD for the same restaurant, implying about 30 percent higher revenue per seat‑hour at dinner.[^19]

You will need to measure Mumbai‑specific daypart RevPASH from POS data; you can use “dinner ≈ 1.2–1.4× lunch RevPASH” as a soft prior but it is **not India‑validated**.[^19]

***

## Channel performance benchmarks (open, engagement, ROI)

There is **no comprehensive India‑restaurant‑only panel** for WhatsApp/SMS/email/ads; most metrics come from:

- Indian martech vendors reporting blended India numbers across verticals.
- Global F\&B SMS benchmarks (mostly US).
- Platform case studies (often e‑commerce, not restaurants).

I’ll separate by channel and flag clearly.

### WhatsApp Broadcast (INDIA‑HEAVY, cross‑vertical)

- Multiple India‑focused sources report **read/open rates above 90–98 percent** for WhatsApp campaigns.[^20][^21][^22][^23]
- WebEngage notes read rates above 90 percent and click‑through rates (CTR) around 40–50 percent “in most cases.”[^20]
- An Indian marketing piece comparing channels reports WhatsApp at **about 98 percent open rate and 45–60 percent CTR**, versus email 15–25 percent open and 2–5 percent CTR.[^22]
- Another India platform (AiSensy) claims both WhatsApp and SMS have ≈98 percent open rates, but WhatsApp delivers **45–60 percent CTR vs SMS 2–6 percent CTR**, and cites specific Indian brands achieving 15–150× ROI on WhatsApp campaigns (non‑F\&B).[^23]

**F\&B‑specific:** I did not find a credible published figure like “WhatsApp broadcast lifts restaurant repeat visits by X percent in India.” A LinkedIn case‑study of an Indian restaurant chain using WhatsApp reports:

- Noticeable increase in foot traffic across locations after WhatsApp campaigns combining menu, offers and exclusive promotions.[^13]

…but without hard percentages. Treat repeat‑visit lift as **modelled locally**, not from external benchmarks.

### SMS (GLOBAL F\&B + GENERIC INDIA)

- Global F\&B SMS benchmarks (TextUs) show **average response rates 28–38 percent**, click‑through rates around 12–14 percent, and opt‑out rates around 0.12 percent for accommodation and food services.[^24]
- Generic SMS marketing stats (multi‑industry) commonly quote **≈98 percent open rate**, with response rates 28–45 percent depending on vertical.[^25][^26]

In India, DLT and DND reduce spam, but I could not find **current, India‑F\&B‑specific response rates**. You can safely use:

- Open rate: ≈95–98 percent (GLOBAL/GENERIC).[^26][^25]
- Click/response rate: ≈10–15 percent for tracked links in food/hospitality campaigns (GLOBAL F\&B).[^24]

These should be explicitly marked as **global or cross‑category proxies** in your database.

### Instagram organic (India, multi‑industry; F\&B contextual)

- upGrowth’s India social benchmarks (2026) report that **Instagram Reels engagement in India is around 3.5–5 percent**, while feed posts (images/carousels) average around 1–2 percent engagement.[^27]
- Global datasets (Statista, Socialinsider) show Reels engagement substantially higher than static posts (e.g., Reels from feed at about 6.9 percent engagement vs decreasing engagement for carousels/images in 2024 globally).[^28][^29]

India F\&B operators and RestaurantIndia articles consistently highlight:

- “Instagram‑first food brands” where most discovery and engagement is visual (Reels, stories) rather than text.[^6]

But those trade pieces are qualitative, without numeric engagement splits for Mumbai F\&B pages. Use the **3.5–5 percent Reels vs 1–2 percent feed engagement** as **India‑wide multi‑industry benchmarks** for organic, with the expectation that strong food accounts in Mumbai can outperform this band.[^27]

### Meta / Instagram Ads (CPM/CPC/ROAS) – NO HARD INDIA‑F\&B DATA

I could not find robust, India‑restaurant‑only CPM/CPC/ROAS benchmarks published by Meta, RestaurantIndia, or India agencies in a way that cleanly isolates F\&B.

- Some Indian marketing blogs list general Instagram ad budget ranges and content creation costs but not reliable sector‑level CPM or ROAS for restaurants.[^30]

Given your defensibility requirement, I would **not store any numeric CPM/ROAS for Meta F\&B India from open web sources**; use your own campaign data or agency reports.

### Google Ads – “restaurant near me” conversion (NO INDIA‑F\&B DATA)

Google does not publish India‑specific conversion rates for “restaurant near me” queries, and I found no independent India F\&B panel that quantifies this.

You should treat **any numeric value here as an internal assumption driven by your partner restaurants’ analytics**, not an external benchmark.

### Zomato / Swiggy promoted listings ROI – NO PUBLISHED NUMBERS

Neither Zomato nor Swiggy publishes systematic ROI multipliers for promoted listings (e.g., “X× uplift in orders per rupee spent”) in public investor documents.[^31][^10][^32]

- Trade press sometimes asserts that visibility boosts orders, but without defensible multipliers.
- The Swiggy 2024 recap only quantifies savings and reservations, not paid listing ROI.[^11][^12]

So **do not store any numeric ROI for promoted listings from external sources**; treat this as something you estimate from venue‑level data (baseline vs campaign periods).

### Micro‑influencers (India F\&B / Mumbai)

**Follower range (INDIA BENCHMARK):**

- Influencer discovery tools in India explicitly define micro‑influencers as accounts with **about 1,000–25,000 followers**; for example, Modash lists “micro influencers (defined as 1k–25k followers) with majority audience in Mumbai.”[^33]
- Some pricing guides for India define “micro” more narrowly (1k–10k), but there is consensus that the band is in the low‑thousands to tens of thousands.[^34]

**Cost per post (INDIA BENCHMARK, cross‑category):**

- A 2025 Indian pricing guide suggests **micro‑influencers (1k–10k followers) typically charge ₹1,000–₹10,000 per sponsored post**, with food examples among the use‑cases.[^34]
- Reddit and agency anecdotes for Mumbai mention mid‑tier influencers (hundreds of thousands of followers) charging ₹1–3 lakh per reel, which gives an upper bound for “macro/celebrity” in your pricing curves.[^35]

**ROI multipliers:**

- Academic and global marketing studies sometimes quote **influencer marketing ROI at 11× vs other digital forms**, but this is generic, not India F\&B specific.[^36]
- I could not find a credible, India‑restaurant‑specific citation for “6.5× ROI” for micro‑influencers; treat such a number as **unsubstantiated** unless you get it from a closed‑door agency benchmark deck.

So your defensible database values are:

- Micro‑influencer follower band (India): **1k–25k followers (definition)**.[^33]
- Typical per‑post fee (India, all verticals): **₹1,000–₹10,000** for micro tier.[^34]

Any ROI multiplier should be modelled from restaurant‑side sales data rather than from public sources.

### YouTube Shorts vs Instagram Reels (India food content) – NO HARD DATA

- I did not find India F\&B‑specific comparative engagement data for YouTube Shorts vs Instagram Reels.
- Global data suggests Shorts can match or exceed Reels reach in some verticals, but this is **not India‑restaurant‑specific** and comes mostly from platform‑agnostic social benchmarks, not F\&B.[^29][^28]

Treat Shorts vs Reels performance as a **measurement question for your own content**, not something you can preload from external benchmarks.

***

## Word of mouth (WOM), NPS, repeat visits, loyalty

### WOM / referrals

- A RestaurantIndia piece on word‑of‑mouth marketing for restaurants cites a Nielsen study emphasizing that **recommendations from friends and family are the most trusted form of advertising for restaurants**, but does not quantify “number of people told per satisfied customer.”[^9]
- Broader Nielsen online surveys on eating out note that **96 percent of urban Indians consume food from take‑away restaurants at least once a month and 37 percent at least weekly**, reflecting a large base for WOM but not referral counts per diner.[^14]

There is **no India‑specific, F\&B‑specific estimate** like “an average diner tells 3.4 people”; such numbers in global marketing literature are typically generic and not tied to India or restaurants.

### NPS / referral metrics

I did not find published NPS distributions for Indian restaurants from NRAI or major consultancies. NPS is mainly an internal operator metric.

### Repeat visit rate

Restrofi’s India‑focused metric guide (again, operator heuristic) suggests:

- A **repeat customer rate around 25–35 percent** is “strong” for a neighborhood restaurant, with fine dining and destination venues naturally lower but with higher average order values.[^1]

This is **an India‑context operational benchmark, not a national average**; you can treat 25–35 percent as a “healthy target band” for repeat‑visit share of orders in your models.

### Loyalty programs in Indian restaurants

I did not find large‑sample quantified effects like “loyalty programs increase visit frequency by X percent” for India restaurants.

Qualitatively, Indian restaurant tech (POS and CRM providers) stress:

- Higher repeat order share among loyalty members and lower acquisition cost, but without publicly sharing the underlying numbers.[^37][^1]

For defensibility, treat loyalty uplift multipliers as **to be estimated from client data**, not pre‑filled from external benchmarks.

***

## Dwell time and spend benchmarks (India)

### Dwell time

There is very little structured dwell‑time data for Indian restaurants:

- A RestaurantIndia article with operator interviews gives anecdotal ranges: a casual dining outlet in Goa reports in‑store stays ranging from **5–20 minutes for quick consumption** to “more than 2 hours” for lingerers, highlighting high variance and the lack of standardized dwell benchmarks.[^38]

You should **not treat this as a Mumbai benchmark**; dwell time is best captured from in‑venue telemetry (ordering, payment, Wi‑Fi check‑in/out).

### Average check size (AOV) in India and Mumbai

- NRAI/TimesNow reporting based on IFSR 2024: Mumbaikars spend **about ₹877 per restaurant visit per capita**, with an average frequency of 7.92 non‑home‑cooked food occasions per month; a large part of this is online orders.[^2]
- For NCR, another NRAI‑based article reports **Delhi consumers spend about ₹1,165 per month on eating out**, with a national per‑person average dine‑out and ordering‑in frequency of 3.7 and 4.2 per month respectively.[^39][^3]

Restrofi’s India benchmarks (operator heuristic) suggest:

- Casual Indian restaurant AOV: **₹280–450** per order in Tier‑2 cities; premium urban restaurants targeting **₹600–1,200+** per order.[^1]

These AOV values are **not Mumbai‑exclusive**, but they sit in a plausible band relative to the NRAI per‑visit spend for Mumbai (₹877) and Delhi (₹1,165), which include both casual and premium occasions.[^39][^2]

### Spend mix (food vs alcohol vs dessert) and dessert attach rate – NO INDIA DATA

I could not find any credible India‑wide, city‑specific data that breaks an average restaurant check into food vs alcohol vs dessert share, nor any robust “dessert attach rate” statistics (e.g., “dessert ordered in 18 percent of visits”).

Any such metrics will need to be derived from POS data; global studies are too context‑dependent to import directly.

***

## Segment‑specific insights

### Working women dining out (India)

No quantitative public data broken out as “professional women in Indian cities” for:

- Dining frequency.
- Platform preference.
- Average spend.

However, NRAI IFSR and hospitality industry commentary point to:

- Rising female workforce participation in urban India and increased demand for safe, comfortable dining environments in metros, which in turn drives growth of cafés, QSRs and organized casual dining where safety and ambience are emphasized.[^4][^16]

Given the lack of numeric splits, treat “working women” as a **behavioral overlay** on office‑worker and premium segments rather than a separately benchmarked market.

### Solo dining

- RestaurantIndia’s WOM article notes that **solo dining is rapidly becoming more common in India’s social dining culture**, especially in urban areas, but does not give a percentage of visits or diners.[^9]

Swiggy and Zomato annual “How India Eats”‑type reports describe:

- High dinner and late‑night ordering volumes, and growing experimentation among young urban consumers, but do not label what share are solo orders versus group orders.[^40][^12][^31]

So solo dining should be labeled as **“growing trend” (qualitative)**, not quantified, in your database.

### Premium dining: market size and growth (Mumbai)

- Market‑research firms estimate the **India full‑service restaurants market** at about 42.1 billion USD in 2026, growing at roughly 11 percent CAGR toward 2031.[^41]
- The **India cafés and bars market** is projected to grow from about 20.5 billion USD in 2026 to 31.5 billion USD by 2031 at 8.9 percent CAGR.[^42]

These are **national level**; no breakdown is publicly available that cleanly isolates “premium casual + fine dining Mumbai” as a specific revenue pool. You would need to apply your own city share/format share assumptions using NRAI city‑level market shares (paywalled) and treat them as internal estimates, not external benchmarks.

### College / youth (18–25) dining frequency and spend

Most of the detailed “youth” data in the open web is dated but still directionally useful:

- A RestaurantIndia consumer‑segment study on “aspiring adolescents” (14–17, not employed) found that **about 61 percent eat out once a week, and about 30 percent more than twice a week**, in metros/mini metros/Tier‑1 cities (2014).[^15]

NRAI’s newer IFSR data shows:

- Overall India average non‑home‑cooked occasions at **7.9 per month** in 2023–24 across the population; youth segments tend to be above this but public data doesn’t break that out.[^3]

Due to age and lack of segmentation in recent reports, I would:

- Use the 2014 study only as **qualitative support** for “high eating‑out frequency among urban youth”.[^15]
- Rely on your own Mumbai data for hard frequency and spend metrics by age segment.

***

## What you can safely put in your database now

Given your “defensible number” requirement, here’s the subset that is robust enough to ingest as **external facts**:

1. **Macro \& frequency (INDIA DATA)**
    - India food‑services market size and CAGR from NRAI IFSR 2024.[^5][^4]
    - India average dine‑out (3.7) and order‑in (4.2) occasions per month per person, and 7.9 total non‑home‑cooked occasions (2018–19 vs 2023–24 trend).[^3]
    - Mumbai average non‑home‑cooked frequency (7.92 per month) and per‑visit spend (₹877 per capita).[^2]
2. **RevPASH \& AOV (INDIA BENCHMARK, clearly labelled)**
    - Restrofi RevPASH target bands: casual dine‑in ₹80–150, fine dining ₹200–400.[^1]
    - Restrofi AOV bands: casual ₹280–450, premium urban ₹600–1,200+.[^1]
3. **Channel performance (INDIA‑HEAVY / GLOBAL with flags)**
    - WhatsApp: open rates ≈90–98 percent; CTR ≈40–60 percent across campaigns in India.[^21][^22][^23][^20]
    - SMS (global F\&B): open ≈95–98 percent; CTR ≈12–14 percent; response rate ≈28–38 percent.[^25][^24]
    - Instagram organic (India): Reels engagement ≈3.5–5 percent vs 1–2 percent for feed posts across industries.[^27]
4. **Influencer definitions \& costs (India)**
    - Micro‑influencer follower band: **1k–25k followers** with majority audience in Mumbai/India.[^33]
    - Micro‑influencer cost: **₹1,000–₹10,000 per post** for 1k–10k accounts (cross‑category).[^34]
5. **Repeat‑rate benchmark (INDIA BENCHMARK)**
    - “Healthy” repeat customer rate (order share from returning guests) around **25–35 percent** for Indian neighborhood restaurants.[^1]

Everything else — platform‑by‑segment usage, WOM referral counts, loyalty uplift, Shorts vs Reels, Google Ads conversion, Zomato/Swiggy promotion ROI, fine‑grained spend mix — should be stored either as:

- Categorical/ordinal assumptions (like the platform‑behavior matrix above), or
- Empty fields waiting for your own measurement.

If you’d like, I can next design a **schema‑ready table layout** (one tab for “hard external benchmarks”, one for “operator heuristics”, one for “Polynovea assumptions”) so you can load this cleanly into your venue‑intelligence database and then progressively overwrite heuristics with your own Mumbai data.
<span style="display:none">[^100][^101][^102][^103][^104][^105][^106][^107][^108][^109][^110][^111][^112][^113][^114][^115][^116][^117][^118][^119][^120][^121][^122][^123][^124][^125][^126][^127][^128][^129][^130][^131][^132][^133][^43][^44][^45][^46][^47][^48][^49][^50][^51][^52][^53][^54][^55][^56][^57][^58][^59][^60][^61][^62][^63][^64][^65][^66][^67][^68][^69][^70][^71][^72][^73][^74][^75][^76][^77][^78][^79][^80][^81][^82][^83][^84][^85][^86][^87][^88][^89][^90][^91][^92][^93][^94][^95][^96][^97][^98][^99]</span>

<div align="center">⁂</div>

[^1]: https://restrofi.com/blog/restaurant-analytics-metrics-track

[^2]: https://www.timesnownews.com/lifestyle/food/news/nrai-issue-a-report-says-delhi-mumbai-hyderabad-sees-a-surge-dinning-outside-article-111749069

[^3]: https://www.linkedin.com/posts/technopak-advisors_foodservices-annualgrowth-frequency-activity-7218532269207040000-E31Q

[^4]: https://nrai.org/aboutNewsAndUpdate.aspx?ID=6EQtfBjriLQ%3D\&Type=oS9yZygW1hU%3D

[^5]: https://economictimes.indiatimes.com/industry/services/hotels-/-restaurants/indias-food-services-sector-to-hit-rs-7-76-lakh-cr-by-2028-nrai-report/articleshow/111609132.cms

[^6]: https://www.restaurantindia.in/article/zomato-vs-swiggy-which-platform-is-better-for-restaurants.16018

[^7]: https://redseer.com/reports/the-big-bite-scaling-success-in-indias-food-services/

[^8]: https://www.scribd.com/document/845240836/NRAI-report

[^9]: https://www.restaurantindia.in/article/why-word-of-mouth-is-the-best-marketing-tool-for-restaurants.14195

[^10]: https://b.zmtcdn.com/investor-relations/Zomato_Annual_Report_2022-23.pdf

[^11]: https://www.indiatimes.com/trending/year-ender-2024-heres-what-india-ate-according-to-swiggys-2024-data-649027.html

[^12]: https://mediabrief.com/how-india-swiggyd-its-way-through-2024/

[^13]: https://www.linkedin.com/pulse/using-whatsapp-drive-local-business-growth-india-karthik-korukonda-

[^14]: https://www.scms.edu.in/uploads/journal/articles/article_27.pdf

[^15]: https://www.restaurantindia.in/article/eating-out-behavior-of-consumer-segments.6130

[^16]: https://www.restaurantindia.in/article/how-data-is-defining-the-future-of-restaurants.15788

[^17]: https://www.siteminder.com/r/revpash/

[^18]: https://restaurantbookingsystem.com/academy/glossary/revpash/

[^19]: https://lavu.com/revpash-essential-formula-restaurant-managemen/

[^20]: https://webengage.com/emagazine/experts-speak/whatsapp-marketing-expert-insights-revealed/

[^21]: https://www.wishtreeinfosolutions.com/case-study-on-whatsapp-marketing/

[^22]: https://www.wassy.in/whatsapp-vs-email-vs-sms-marketing-2025

[^23]: https://m.aisensy.com/blog/whatsapp-marketing-vs-sms-marketing/

[^24]: https://textus.com/sms-benchmarks/sms-benchmarks-for-food-beverage

[^25]: https://d7networks.com/blog/sms-marketing-statistics-you-must-know/

[^26]: https://txtcart.ai/blog/text-marketing-statistics/

[^27]: https://upgrowth.in/social-media-engagement-rate-benchmarks-india-2025/

[^28]: https://www.statista.com/statistics/1353273/instagram-post-interaction-by-format/

[^29]: https://www.socialinsider.io/social-media-benchmarks/instagram

[^30]: https://wingcomm.co/blogs/instagram-marketing-cost-india-2025/

[^31]: https://b.zmtcdn.com/investor-relations/Zomato_Annual_Report_2023-24.pdf

[^32]: https://simplehai.axisdirect.in/images/ResearchPDF/2023/Zomato-InitiatingCoverage_31072024.pdf

[^33]: https://www.modash.io/find-influencers/india/mumbai/micro

[^34]: https://wdcweb.com/blog/influencer-marketing-costs-in-india/

[^35]: https://www.reddit.com/r/mumbai/comments/1fndnzi/what_are_the_typical_fees_for_paying_influencers/

[^36]: https://managementdynamics.researchcommons.org/cgi/viewcontent.cgi?article=1316\&context=journal

[^37]: https://billfeeds.com/blog/restaurant-data-analytics-reports.html

[^38]: https://www.restaurantindia.in/article/what-s-an-average-halt-of-a-customer-at-your-restaurant.6664

[^39]: https://www.millenniumpost.in/delhi/ncr-has-the-food-market-size-of-rs-42000-cr-states-nrai-report-571403

[^40]: https://blog.swiggy.com/news/how-india-swiggyd-its-way-through-2024-a-deep-dive-into-the-nations-eatopia/

[^41]: https://www.mordorintelligence.com/industry-reports/india-full-service-restaurants-market

[^42]: https://www.mordorintelligence.com/industry-reports/india-cafes-\&-bars-market

[^43]: https://www.scribd.com/document/984126299/India-Food-Service-Market-trend-and-Swiggy-report

[^44]: https://www.leaglobal.com/resource/selling-merchandise-online-in-india--market-entry-strategy--tax-liability--regulations.html

[^45]: https://www.facebook.com/westinpune/posts/westinpune-announces-the-𝗮𝗽𝗽𝗼𝗶𝗻𝘁𝗺𝗲𝗻𝘁-𝗼𝗳-𝗻𝗲𝘄-𝗹𝗲𝗮𝗱𝗲𝗿𝘀𝗵𝗶𝗽westinpune-announces-the-a/872711968216695/

[^46]: https://nrai.org/BookYourCopy.aspx

[^47]: https://www.instagram.com/p/DTKgYQ6E0qn/

[^48]: https://christuniversity.in/uploads/departmentmiscellaneous/BHM Syllabus AY 2024-25_20251028051445.pdf

[^49]: https://www.restaurantindia.in/article/india-to-be-the-3rd-largest-food-service-market-by-2028-overtaking-japan-nrai-ifsr-2024

[^50]: https://www.facebook.com/EconomicTimes/posts/-your-food-order-just-got-futuristic-swiggy-now-lets-users-order-food-using-chat/1372501698239068/

[^51]: https://www.linkedin.com/in/gopu-nayar-717276a

[^52]: https://www.linkedin.com/pulse/event-highlights-unveiling-nrai-indian-food-services-report-gandhi-ulgae

[^53]: https://www.facebook.com/RestaurantIndia/posts/hotelnewsnovotel-mumbai-juhu-beach-has-announced-the-appointment-of-rajnish-shar/1258263263010792/

[^54]: https://www.ijfmr.com/papers/2025/5/58839.pdf

[^55]: https://www.facebook.com/ETinsights/posts/indias-food-delivery-giants-are-adding-a-health-angle-to-their-apps-zomato-found/1387169000079938/

[^56]: https://christuniversity.in/uploads/departmentmiscellaneous/AY- 2023-24 SYLLABUS_20240429114028.pdf

[^57]: https://www.slideshare.net/slideshow/zomato_annual_report_2022-23-true-and-originalpdf/275095778

[^58]: https://www.scribd.com/presentation/857450596/Zomato-Case-Study

[^59]: https://www.instagram.com/p/DWGOhvtkiWJ/

[^60]: https://redseer.com/wp-content/uploads/2025/01/the-big-bite-scaling-success-in-indias-food-services.pdf

[^61]: https://www.scribd.com/document/905767535/Redseer-3MQ-Report-Macro-Model-Markets-Quotient-2025-1

[^62]: https://ijsrem.com/uploads/production/Exploring-the-Segments-Growth-Drivers-and-Future-Trends-of-Indias-Food-Service-Industry.pdf

[^63]: https://www.scribd.com/document/756994798/ANNUAL-ZOMATO-FINAL

[^64]: https://www.instagram.com/p/DVQFQiAE8rd/

[^65]: https://assets.kpmg.com/content/dam/kpmg/in/pdf/2016/11/Indias-food-service.pdf

[^66]: https://www.instagram.com/reel/DVL9S0IjD3C/

[^67]: https://www.linkedin.com/posts/gyandeep-singh-7b03b216_rooms-revenue-model-fb-revenue-model-other-activity-7397159995110354944-lihn

[^68]: https://www.remshospitality.com/blog/revpash-the-unknown-but-most-effective-restaurant-kpi

[^69]: https://loopmenu.in/restaurant-revenue-calculator

[^70]: https://www.instagram.com/reel/CY5ITXvla01/

[^71]: https://www.altexsoft.com/glossary/revpash/

[^72]: https://www.linkedin.com/posts/edward-maria-dass-73055740_apc-stands-for-average-per-cover-the-average-activity-7397472868172849152-U9wR

[^73]: https://www.sciencedirect.com/science/article/pii/S0278431925000398

[^74]: https://www.linkedin.com/posts/arpit-rawat-bbb248219_knowledge-revpash-hotel-activity-7340214919029542912-pf5v

[^75]: https://www.tiktok.com/@owner_dot_com/video/7610853034771418381

[^76]: https://www.paperchase.ac/accounting/understanding-hospitality-data-analytics/

[^77]: https://www.instagram.com/p/DXpkOFiiHwR/

[^78]: https://flipmenu.app/es/blog/restaurant-analytics-metrics-guide

[^79]: https://revenue-hub.com/revpash-restaurant-revenue-management/

[^80]: https://www.hc-resource.com/post/restaurant-ops-in-2025-the-9-kpis-every-gm-should-be-tracking-weekly-rewrite

[^81]: https://revenue-hub.com/grow-your-restaurant-revenue-with-the-revpash-formula/

[^82]: https://www.hc-resource.com/copy-of-posts/top-9-restaurant-kpis-to-track-for-profit-in-2025

[^83]: https://www.facebook.com/chefananyabanerjee/posts/i-was-invited-by-nrai_india-the-national-restaurant-association-of-india-nrai-to/1000348958220383/

[^84]: https://restaurantbookingsystem.com/academy/revpash/

[^85]: https://sevenrooms.com/blog/restaurant-revpash/

[^86]: https://www.youtube.com/watch?v=P8flTZ6sYNs

[^87]: https://www.amity.edu/gurugram/jccc/pdf/dec-5.pdf

[^88]: https://www.instagram.com/reel/DItXL3WCMn2/

[^89]: https://erp.bharati.du.ac.in/smartprof/file_uploads/tmpFile/20/proofOfArticle_1748368119.pdf

[^90]: https://indiantelevision.com/news-headline/2024-indians-placed-29-per-cent-more-dinner-orders-than-lunch-on-swiggy/

[^91]: https://www.instagram.com/p/DRUYFChllQR/

[^92]: https://www.instagram.com/p/DT9f_cYkZJ5/

[^93]: https://www.republicbiz.com/news/indians-ordered-two-biryanis-every-second-on-swiggy-interesting-facts-from-swiggy-s-2024-roundup-report

[^94]: https://www.facebook.com/100063991871591/posts/the-food-delivery-sector-now-has-scale-users-and-demand-across-citieswith-millio/1401859188623797/

[^95]: https://www.sciencedirect.com/org/science/article/pii/S1947959X22000304

[^96]: https://www.linkedin.com/pulse/rise-whatsapp-marketing-gcc-restaurant-industry-resto-guru-1c3wf

[^97]: https://whatsappbusiness.com/resources/success-stories/

[^98]: https://www.spurnow.com/en/blogs/whatsapp-marketing-india

[^99]: https://www.restaurantindia.in/article/restaurant-marketing-strategies-that-actually-work-in-india.16069

[^100]: https://www.linkedin.com/pulse/top-10-micro-food-bloggers-mumbai-find-collab-5u82f

[^101]: https://influcollabs.com/city/Mumbai

[^102]: https://www.instagram.com/reel/DQraAreiMcN/

[^103]: https://blog.hootsuite.com/average-engagement-rate/

[^104]: https://www.modash.io/find-influencers/india/mumbai/food

[^105]: https://findcollab.com/blog/top-10-micro-food-bloggers-in-mumbai

[^106]: https://www.sprinklr.com/blog/instagram-statistics/

[^107]: https://collabr.in/category/Food/city/Mumbai/

[^108]: https://wanotifier.com/whatsapp-marketing-campaign-examples/

[^109]: https://digitalcourseai.in/zomatos-targeted-marketing-strategy-case-study-swot-breakdown-visual-infographics/

[^110]: https://www.restaurantindia.in/article/10-best-instagram-marketing-strategies-for-restaurants.13254

[^111]: https://www.scribd.com/document/1008835209/Zomato-Business-Case-Study

[^112]: https://www.foodics.com/restaurant-marketing-strategies-email-vs-sms-vs-social/

[^113]: https://www.restaurantindia.in/article/how-to-effectively-market-your-restaurant.13102

[^114]: https://launchlify.com/zomato-business-model-case-study/

[^115]: https://bestow.in/best-marketing-channel-whatsapp-or-email

[^116]: https://www.restaurantindia.in/article/email-marketing-strategies-for-restaurants-to-drive-repeat-customers-email-is-still-the

[^117]: https://www.webmarketingacademy.in/digital-marketing-blogs/zomato-marketing-strategy-case-study-2024/

[^118]: https://magictext.in/bulk-sms-vs-whatsapp-marketing-roi/

[^119]: https://www.restaurantindia.in/article/easy-ways-to-attract-more-customers-during-slow-nights.13306

[^120]: https://www.restaurantindia.in/article/how-vendor-relationships-are-driving-restaurant-growth.16067

[^121]: https://www.shopify.com/in/enterprise/blog/influencer-marketing

[^122]: https://www.jigsawkraft.com/post/influencer-marketing-cost-in-india-complete-2026-pricing-guide

[^123]: https://www.adgully.com/date/23-01-2026

[^124]: https://www.restaurantindia.in/article/10-restaurant-marketing-ideas-that-are-wasting-your-money.13621

[^125]: https://www.linkedin.com/in/sukanya-mohapatra

[^126]: https://www.instagram.com/p/DWohOWElX9B/?hl=en

[^127]: https://economictimes.com/industry/services/hotels-/-restaurants/heres-what-delhi-and-mumbai-love-to-eat-nrais-comprehensive-food-order-report/articleshow/111869204.cms

[^128]: https://economictimes.indiatimes.com/industry/services/hotels-/-restaurants/dining-out-surges-in-india-upi-payments-jump-34-as-restaurants-see-record-sales/articleshow/124769936.cms

[^129]: https://www.restaurantindia.in/article/the-cost-of-building-a-restaurant-in-metro-cities-in-india.13311

[^130]: https://www.posist.com/restaurant-times/resources/complete-guide-opening-restaurant.html

[^131]: https://www.travelfoodservices.com/tfscms/uploads/industryreports/industryreports_1751610522.pdf

[^132]: https://www.earthvagabonds.com/food-prices-in-india-for-slow-budget-travelers/

[^133]: https://www.theleela.com/prod/content/assets/2025-05/Industry Report (Update) - 09May2025.pdf?VersionId=5Q4MxYyh.N5k.D.0YSmeQb4ITqh1m0lL

