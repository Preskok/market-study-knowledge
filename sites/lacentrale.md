# lacentrale (FR)

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- Declining yield across Mar 2025 (155k→72k at 13:00).
- Listings-only crawler.
- Uses `first-id` tracking (https://whatismy.first-id.fr/) — cross-web user ID system. Relevant for anti-bot fingerprinting.
- Nov 2024: crawl every 3 days reliably gets ~300k/320k (90%+). Even crawl schedule prevents heavy consumption.
- Oct 2024 ScraperAPI notice: "heavily protected — requires Ultra Premium Proxies" → 75 credits per request (3× higher than prior). Disabled when cost-vs-value flips.
- **First registration date unreliable** (April 2023): Real values historically in JS `tc_vars` analytics variable. Site moved/faked values over time. As of April 2023, only one location remained. Monitor for sudden date zeroing.
- **Energy class mapping bug** (June 2023): EU energy label codes in crawler were outdated. Example: site class `G` was stored as `J`. Fix: align with current EU energy label standard (A–G scale updated vs old A–J).


<!-- merged from second source section -->

- June 27 2024: crumbler enabled → more vehicles but 90% of requests blocked for pages > 20. Only 25% of tasks completed in 16h.
- June 28 2024: site switched ALL traffic to new HTML structure mid-day — critical selector change → hotfix required same day (Marko).
- July 30 2024: another critical selector change → hotfix same day.
- Oct 2024: Ultra Premium (75 credits/request) required. first-id tracking.
- Own queue `MS_LACENTRALE_LISTING_URLS_TO_FETCH` (3 consumers), created Sept 2024.
- Pattern: gets blocked frequently. Single consumer keeps pressure low.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->
