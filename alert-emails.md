# Alert Emails — Decoding Guide

## Senders

| Sender | Source |
|---|---|
| `graylogprod@b2b-carmarket.com` | Graylog streams — log-based |
| `Marketstudy Notifications <system@preskok.si>` | AMS custom — cron jobs, reports |

Both trigger false alarms when Graylog is down (alerts are log-based, not ES-data-based).

---

## Subjects

### `Problem preparing listingUrl messages for site [SITE]`
Producer threw in `getBrandsAndModels()` or initial request. **Auto-retry: 6/7/8 AM.** Check Graylog for stack.

### `Prepared listingUrl messages 0 for site [SITE]`
Producer ran without error, 0 listings — silent selector failure. **NO auto-retry.** Manual fix.

### `[SITE] has N% LESS/MORE vehicles than yesterday`
Count comparison. **False alarm common** — small sites fluctuate; legit stock changes; RMQ channel restart can inflate.

### `Big number of validation logs for site(s)` + property breakdown
Many vehicles had field value changes. **False alarm common:**
- `null → value`: recovery post-fix — EXPECTED
- `value → null`: regression — investigate
- `value1 → value2`: site changed (e.g. `aygo` → `aygo x`) — usually legit

### `Report: Data vehicles failed validations`
Values failed ES validation (HP too big, price too big, mileage null). Parser fix or sanitization.

### `Alert: Details URLs validation failed for site(s)`
Detail visits failed validation. Common: anti-bot block, URL change with redirects. Known blocked: `skipDetailsUrlValidation: true`.

### `Urgent: N queue(s) did not receive any listing urls`
Producer didn't write to RMQ. **False alarm HIGH** — especially when Graylog down. Verify via ES actual count.

### `Crawling not finished`
Consumers still running past threshold. Check queue depth, stuck messages, timeout loops.

### `N queue(s) not empty` (12h)
Stuck messages. Check for timeout loops. Note: `MS_WEEKLY_...` not empty Tue-Sun is normal; `MS_HUNGARY_...` not empty in morning is normal.

### `Graylog request timed out`
Reports can't reach Graylog. Infra — `#tt-devops-support`.

### `Urgent: Marketstudy will probably not crawl`
test-crawl endpoint failed — often triggered by accidental stage test.

### `Vehicle S3 vs ES comparison failed in object prop`
Marko's S3-vs-ES validation script. Field silently dropped by ES validator (too-many-doors, engineCapacity overflow, price too big). Parser should sanitize.

### `ALL error logs` (weekly)
Summary of all errors. Fires on disabled crawlers too — report bug, not crawler bug (known issue).

### `Problems in getting URLs for details URLs validation`
Fires on non-crawl days of multi-day crawlers (<5 vehicles in last 2 days). Not a bug.

---

## False-alarm: Graylog down

**Signals:** Email claims no messages/logs/reports; multiple queues affected; ES counts normal.

**Diagnosis:** Check `#tt-devops-support`. Check Kibana (reads ES directly) for counts.

**Action:** No fix. Document.

---

## False-alarm: Small site fluctuation

**Signals:** Drop 20-50% on site <500 vehicles, no errors, recovers 1-3 days.

**Known fluctuators:** auto-elite, autohaus-listle, rastetter, autobazar, brie-des-nations, cardoen, oxylio, vo3000, glinche-automobiles, eurostocks, schmidt-automobile.

---

## False-alarm: Outlook / mail client

**Signal:** Matea found daily emails missing until she restarted Outlook.

**Action:** Always verify your mail client before assuming reports aren't being sent.

---

## False-alarm: Validation spike on index rebuild

**Signal:** Huge SVL spike day of Data index rebuild.

**Action:** Expected for 2 days after remap — all 6.5M active vehicles re-validated.

---

## Cadence

- Daily: vehicle count comparison (morning), validation logs
- 12h: queues not empty check
- Evening: crawled-vehicles-comparison report
- Weekly: AWS cost, scraper credit checks
- Monthly: stock widget 2x, ALL error logs 1x, AWS cost 1x

Team tracks in weekly Slack thread (`#tt-market-study-checklist`). On-call person documents findings.

---

## Escalate to `#tt-devops-support`

- Graylog down
- Proxy ports down (`9007` especially)
- MySQL `ECONNREFUSED`
- AWS S3 permission issues
- Full Graylog retention issue

Ping: Stas (infra owner).
