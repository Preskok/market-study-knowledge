# Queue Health Rules

Rules are applied in order — first matching block wins. Fall through to DEFAULT for any unmatched MS_* queue.

Time-aware rules use `date +%u` (1=Mon … 7=Sun) and `date +%H` (hour 00–23).

---

## MS_DL
**Rule:**
- 🟢 = messages == 0
- 🔴 = messages >= 1
**Note:** no-TTL DL — manual purge needed
**Action:** Check Graylog for root cause, then purge or redeliver to original queue.

---

## MS_BULK_DL
**Rule:**
- 🟢 = messages < 500
- 🟡 = 500 ≤ messages ≤ 5000 — DL growing, watch ES
- 🔴 = messages > 5000 — DL flooding, check workers
**Note:** 24h TTL — low counts are mostly dedup noise
**Action (🔴):** Check bulk save worker logs for ES/MySQL connection errors.

---

## MS_BULK_SAVE_DL
**Rule:**
- 🟢 = messages < 500
- 🟡 = 500 ≤ messages ≤ 5000 — check ES workers
- 🔴 = messages > 5000 — workers failing, urgent
**Note:** ES/MySQL connection issues in bulk save workers
**Action:** Check bulk save worker logs.

---

## MS_TASKS_DL
**Rule:**
- 🟢 = messages == 0
- 🟡 = 1 ≤ messages ≤ 10 — some tasks timed out
- 🔴 = messages > 10 — many task failures
**Note:** long-running task DL (e.g. car-gr >2.5h timeout)
**Action:** Check which site's task timed out.

---

## MS_WEEKLY_LISTING_URLS_TO_FETCH
**Time-aware rule:**
- 🟢 = day is Tue–Sun (2–7), any count — car-gr weekly cycle active
- 🟢 = day is Mon (1) AND hour < 23 — purge hasn't run yet
- 🟡 = day is Mon (1) AND hour >= 23 AND messages > 0 — should have purged at 23:25
**Note:** car-gr only — Tue start → drains across week → Mon 23:25 purge

---

## MS_HUNGARY_LISTING_URLS_TO_FETCH
**Time-aware rule:**
- 🟢 = hour < 23 OR (hour == 23 AND minute < 30), any count — fill or active crawl
- 🟡 = hour >= 23 AND minute >= 30 AND messages > 0 — should have purged at 23:25
**Note:** mobile-bg (matchingDay 0) + hasznalt-auto (matchingDay 1), nightly purge 23:25

---

## DEFAULT
**Applies to:** all MS_* queues not matched above
**Rule:**
- 🟢 = messages ≤ 10000 AND consumers > 0
- 🟡 = messages > 10000 OR (messages > 0 AND consumers == 0)
- 🔴 = messages > 50000
**Note:** generic listing / bulk save queue
