# automobile

## Current status
_Needs manual triage — see history below and update this line when you know the current state._

## History & quirks (newest first where known)
- First API request 404 (MAR-1747).
- **Jan 2023: Full site redesign** — moved to a public API. The old HTML crawler (getBrandsAndModels + listing/detail URLs) completely broke. New ad IDs issued → historical URL matching not possible. Required full rewrite as API crawler.
- **~10% vehicles unreachable** (April 2023): ~10% of ads exist only on brand-level listing (e.g. `?make=11`) but not on any brand+model sub-listing. These are missed by the brand+model crawl strategy. Decision: tolerate this loss rather than adding extra brand-level crawl step.
- **March 2023**: Matea also noted that `automobile.at` has a sub-site pattern — `degeneve-cars.ch/catalogue` was a pure iframe linking to autoscout-ch. Check any new AT site for iframe patterns before implementing crawler.

## Related patterns
_Cross-referenced in failure-patterns.md. Grep that file for this site's name to find them._

---

<!-- Maintenance:
When you add a new entry, put it at the TOP of the history section with a date.
Use format: **YYYY-MM-DD** — what happened + outcome.
When a site is disabled or an issue is resolved, update the "Current status" line.
-->
