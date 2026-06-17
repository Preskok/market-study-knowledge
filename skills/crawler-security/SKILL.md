---
name: crawler-security
description: >
  ALWAYS invoke this skill when the user's message starts with "crawler-security" followed by
  anything — e.g. "crawler-security autowereld", "crawler-security garage-lecat".
  Also triggers on: "check security for <site>", "test security of <site>", "what security does
  <site> have", "can we crawl <site>", "is <site> protected", assessing a new crawl candidate.
  Guides a structured cheapest-to-most-expensive assessment flow and produces a validation table row.
---

# Crawler Security Assessment

Assess a new candidate crawl site for bot protection, proxy compatibility, and crawl feasibility. Work through steps **cheapest → most expensive**. Stop as soon as all 4 routes pass.

**Always test all 4 routes:** brands & models · listing page · vehicle detail · homepage  
**For API crawlers:** test API endpoints, NOT html URLs (autopilot trap)

---

## Step 0 — Pre-step

Determine HTML vs API **per route** — check browser Network tab (XHR/fetch calls). See [guide](https://preskok.atlassian.net/wiki/spaces/M/pages/2913075202).

| Route | HTML | API |
|---|---|---|
| **Brands & models** | Listing URLs generated from HTML page | Listing URLs come from a JSON/API response |
| **Listings** | Vehicle listing data parseable from HTML | Vehicle data comes from a JSON/API response |
| **Details** | Vehicle detail data parseable from HTML | Vehicle data comes from a JSON/API response |

Report format: `b&m: html, listings: api, details: html` (one entry per route that differs)

- Does pagination exceed 100 pages? → crumbler likely needed.

## Step 1 — robots.txt

```bash
curl {baseUrl}/robots.txt
```

Note disallowed patterns for listing/detail paths. Disallowed ≠ illegal — note for awareness only.

## Steps 2–8 — Request methods (cheapest → most expensive)

| Step | Method | Cost | Requires |
|---|---|---|---|
| 2 | `curl {url}` | free | — |
| 3 | `curl -x http://proxy.b2b-carmarket.eu:8000 {url}` | free | office network / VPN |
| 4 | Postman (disable cookie jar, strip headers, try UA variants) | free | — |
| 5 | `curl` with cookies from browser/Postman session | free | — |
| 6 | Puppeteer stealth (`puppeteer-extra` + `puppeteer-extra-plugin-stealth`) | free | — |
| 7 | Puppeteer + proxy (`--proxy-server=http://proxy.b2b-carmarket.eu:8000`) | free | office network / VPN |
| 8 | ScrapeDo: 1 credit → 10 credits → 25 credits | paid | — |

**curl with cookies (Step 5):**
- Copy cookies from a successful browser or Postman session (`Cookie:` header)
- Cookies may be IP-bound (Akamai `ak_bmsc`/`bm_sv`) — must curl from the same IP they were issued on
- If cookies work: note which ones are actually required by removing them one-by-one

**Puppeteer notes (Steps 6–7):**
- Zero cookies needed if stealth passes Akamai/CF — test with no cookies first
- For GDPR consent walls: stealth auto-handles; or call `redirect()` directly from consent page JS
- Cookies are IP+TLS fingerprint bound — cannot be reused in curl/axios
- For API crawlers: intercept XHR via `page.on('response', ...)`

## Step 9 — Security provider detection

| Provider | How to detect | Bypass |
|---|---|---|
| **Akamai** | Cookies `ak_bmsc`, `bm_sv` | Puppeteer stealth |
| **Cloudflare** | `CF-Ray` header, `__cf_bm` cookie, network tab | Puppeteer stealth (lower tiers) |
| **Datadome** | `datadome` cookie, `dd_*` in JS vendors | Hard — ScrapeDo 10–25cr |
| **Cloudfront** | `x-cache: Hit from cloudfront` header | Usually ok; rate-limit risk |
| **GDPR wall** | 302 redirect to consent domain | Puppeteer stealth auto-handles |

## Step 10 — Auth / bearer token

- Test all routes without auth headers — does it work?
- JWT required? Check if token regeneratable without account.
- Account required? Note — may need dealer credentials.

---

## Output — Validation Table Row

Fill in and paste to [cheatsheet](https://preskok.atlassian.net/wiki/spaces/M/pages/2980741121):

```
| {url} | {date} | {robots disallowed patterns or -} | {security provider or -} | {UA required or -} | {crumbler needed?} | {HTML/API/mixed} | {curl ✅/❌} | {proxy curl ✅/❌} | {postman ✅/❌} | {puppeteer ✅/❌} | {cookies needed or -} | {notes} | {your name} |
```

**Notes should include:** minimum ScrapeDo tier if needed · GDPR handling approach · rate-limit unknowns · HTML vs API per route if mixed.

---

## Reference

- Full guide: https://preskok.atlassian.net/wiki/spaces/M/pages/2905243654
- Validation table: https://preskok.atlassian.net/wiki/spaces/M/pages/2980741121
- Proxy: `proxy.b2b-carmarket.eu:8000` (office network / VPN)
