# Local crawler testing recipe

For testing one crawler against the live site without queue volume.

**Tokens & URLs:** All environment-specific values (URLs, access tokens) live in `test/requests/requests_envs/` — use `http-client.env.json` for non-sensitive defaults and `http-client.private.env.json` (gitignored) for real tokens. Never hardcode tokens in docs or code.

**Local API token:** Read from `.env` (`API_TOKEN=...`), **not** from `http-client.env.json` (`accessToken: "asdf"` is a placeholder and returns 401). When scripting curl: `grep -E "^API_TOKEN=" .env | cut -d= -f2`.

**Preferred way to trigger requests:** use the `.http` files in `test/requests/` — they reference env vars automatically. The curl examples below are for quick one-liners only.

---

### 1. Narrow the brand list
Temporarily filter at the end of `getBrandsAndModels()`:
```ts
// TODO temporary test filter — remove before PR
return brandsAndModels.filter(a => a.brandName.toLowerCase().includes('mitsubishi'));
```
Pick a brand with ~500-2000 vehicles — enough to surface bugs, fast enough to iterate.

### 2. Clear stale daily cache (or use a flag)
Use `test/requests/Crawler/Crawler.http` (the `delete-daily-cache` request) or curl with your token from `http-client.env.json`. Wipes ALL sites' cache, not per-site.

**Less destructive alternatives:**
- `AWS_S3_BUCKET_DAILY_CACHE_PERMISSION_WRITE=false` in `.env` — reads still work, writes skipped. **Re-enable before committing.**
- `useS3Cache: false` per `fetchRequest()` call — for one-off requests (required when the request fetches a token that all subsequent requests depend on, otherwise you get a self-loop — gruppo-piccirillo pattern).
- To replay one specific prod response in LocalStack without burning credits: `ams local-testing-flags` or fix-playbook.md.

### 3. Start one or more workers
```bash
APPLICATION_MODE=WORKER npm run start:dev
```
Multiple workers in parallel are fine — port 3000 conflicts on the 2nd+ instance are harmless because the HTTP server fails to bind but RMQ consumers still attach with prefetch=1.

**Watch-mode zombie:** if a worker crashes mid-startup with `EADDRINUSE: 3000`, `nest start --watch` does NOT auto-restart on crash — only on file change. Symptoms: watch process alive, no child, port held. Fix: `lsof -i :3000`, `kill -9 <PID>`, then make a real content change to retrigger.

### 4. Trigger the crawl
Use `test/requests/Crawler/Crawler.http` (the `crawl-brands-and-models` request with your site name), or curl with your token and `workerUrl` from `http-client.env.json`.

### 5. Watch logs
- Local Graylog: `http://graylog.devenv:8090` (token from `.env` — `GRAYLOG_AUTH_TOKEN`)
- Console: `npm run start:dev` streams to terminal
- RMQ UI: `http://localhost:15672` (credentials from `.env`)

### 6. Revert before committing
- Remove the brand filter
- Remove `console.log`s and test data
- Re-enable `AWS_S3_BUCKET_DAILY_CACHE_PERMISSION_WRITE` if you flipped it

### Brand filter caveat on bugfix branches
Some `bugfix/*` branches keep a temporary brand filter ON PURPOSE so stage runs are scoped while iterating. **Don't reflexively remove it — ask first.** The branch owner will tell you when it's time to drop.

---

### Import prod `vehicle_visit` data locally

Export the table from prod as CSV (via DataGrip or similar), place in `/tmp/`. Then:

```bash
# Truncate local table first
mysql -h mysql.devenv -u root -psecret --skip-ssl marketstudy -e "TRUNCATE TABLE vehicle_visit;"

# Import CSV — handles nullable runOnNthDays
mysql -h mysql.devenv -u root -psecret --skip-ssl marketstudy -e "
LOAD DATA LOCAL INFILE '/tmp/<filename>.csv'
INTO TABLE vehicle_visit
FIELDS TERMINATED BY ','
ENCLOSED BY '\"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(storeId, hash, lastVisit, site, @runOnNthDays)
SET runOnNthDays = NULLIF(@runOnNthDays, '');
"

# Verify
mysql -h mysql.devenv -u root -psecret --skip-ssl marketstudy -e "SELECT COUNT(*) FROM vehicle_visit;"
```

CSV must have header row: `"storeId","hash","lastVisit","site","runOnNthDays"`. The `NULLIF` handles empty `runOnNthDays` values (nullable column).

---

### Import prod ES + S3 vehicle data locally (for data-fix testing)

Use when you need realistic prod vehicle data in local ES + S3 to test a data-fix endpoint (e.g. `update-vehicle-urls`).

**One-time setup:** cherry-pick the export/import commit from `feature/no-ticket-s3-import-and-export` onto a TEST branch. See `ams export-import-local-testing` for the full workflow.

**Export (point env at prod):**
```
POST /api/v1/export/vehicles
{ "site": "otomoto", "size": 1000, "dateFrom": "...", "dateTo": "...", "filePath": "./tmp/exports/otomoto.json" }
```
- `dateFrom`/`dateTo` filter on `createdAt` — use the Kibana time range for the problematic vehicles
- File written locally even when `.env` points at prod ES/S3

**Import (point env back to local):**
```
POST /api/v1/data-restore/import-vehicles
{ "filePath": "./tmp/exports/otomoto.json" }
```

**`.env` switching — S3 block:**
The `.env` S3 section has three labeled blocks (LOCAL / STAGE / PROD). Uncomment exactly one block at a time. `AWS_S3_ENDPOINT` must be absent (not empty) for real AWS — Joi rejects empty strings for optional fields. Required bucket vars (RENT, DEALER, SID_DELETED, GENERAL_STORAGE) need non-empty values even if unused — use `prod-unused` / `stage-unused` as placeholders.
