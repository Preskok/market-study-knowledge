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
