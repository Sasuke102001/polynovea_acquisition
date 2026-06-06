# Scraper Field Requirements

Two fields needed per review across all 3 sources:

```
reviewer_name       string  — Display name as shown on platform
reviewer_timestamp  string  — Raw review date, ISO format ("2024-11-15")
                              Keep raw date. Do NOT convert to age_days only.
```

`review_age_days` can stay for backward compatibility but raw timestamp must also be present.

## Per Source

**Google Raw Scrapper** — currently captures neither. Both need to be added.

**Google Places API** — `author_name` and `publish_time` already exist in the API response, just not stored. One-line fix in the fetch script to preserve them.

**MagicPin** — already has `user` (reviewer name). Only `reviewer_timestamp` is missing.

## Notes

- BIF step3 handles everything else: parsing Food/Service/Atmosphere sub-ratings,
  group size, wait time, noise level, price per person from review text.
- Scrapers only need to stop stripping name and date.
- Target: next month's pipeline runs.
