---
name: ams-s3
description: >
  ALWAYS invoke this skill when the user's message starts with "ams-s3" — e.g.
  "ams-s3 https://www.otomoto.pl/...", "ams-s3 ee315ac12567a2b44ae03fc30b093334",
  "ams-s3 stage https://... --write=./response.html", "ams-s3 local <storeId> --delete",
  "ams-s3 prod <url> --date=20260518", "ams-s3" (help).
  This is the Market Study S3 fetcher — pulls raw HTTP responses from the daily cache
  bucket or parsed vehicle/dealer JSON from the store buckets across prod, stage and
  local environments. Replaces the local s3-file-fetcher-gui project. READ works on all
  three envs; WRITE and DELETE are allowed ONLY on stage and local (HARD REFUSED on prod).
  Also triggers on "/ams-s3".
---

# ams-s3 — S3 raw response / vehicle store fetcher

Single-trigger replacement for the legacy `~/Projects/s3-file-fetcher-gui` desktop tool.
Fetch (read), write, or delete S3 objects in the Market Study buckets, with auto-detection
of input shape (URL → daily cache, 32-char hex → store bucket).

## Hard rules

1. **`ams-s3 prod` is read-only.** If env resolves to `prod` AND `--write` or `--delete` is present, refuse immediately, before loading credentials, computing keys, or touching anything. No fallback, no override flag.
2. **Read-only IAM key recommended for `AMS_S3_PROD_*` credentials** in `.env` as belt-and-braces. The skill's refusal is the primary guard.
3. **Never print AWS access keys or secret keys** to chat. Print bucket names, S3 keys, env-var names — never values of `*_KEY_ID` or `*_SECRET_*`.
4. **All env data lives in `~/Projects/market-study/.env`** under `AMS_S3_*` prefixed names. No separate `.env.prod` / `.env.stage` files.

## Invocation forms

| Form | Meaning |
|---|---|
| `ams-s3` | Print this help. |
| `ams-s3 <url>` | READ raw response. env=prod, date=today. |
| `ams-s3 <storeId>` | READ parsed vehicle from prod store. |
| `ams-s3 <env> <input> …` | Env-explicit READ. `env ∈ {prod, stage, local}`. |
| `ams-s3 <env> <url\|storeId> --write=<file>` | WRITE local file at the computed key. **Refused if env=prod.** |
| `ams-s3 <env> <url\|storeId> --delete` | DELETE at the computed key. **Refused if env=prod.** |

### Bucket-selector flags (apply to read, write, delete)

| Flag | Bucket var |
|---|---|
| _(default for storeId)_ | `AMS_S3_${ENV^^}_BUCKET_STORE_VEHICLE` |
| `--rent` | `AMS_S3_${ENV^^}_BUCKET_STORE_VEHICLE_RENT` |
| `--dealer` | `AMS_S3_${ENV^^}_BUCKET_STORE_DEALER` |
| `--deleted` | `AMS_S3_${ENV^^}_BUCKET_SID_DELETED_VEHICLES` |
| `--general` | `AMS_S3_${ENV^^}_BUCKET_GENERAL_STORAGE` (key passed as-is, no hashing) |
| _(default for url)_ | `AMS_S3_${ENV^^}_BUCKET_DAILY_CACHE` |

### Daily-cache extras

- `--date=YYYYMMDD` — override "today" (used in the `YYYYMMDD/<hash>` daily folder).
- `--body='{...}'` — POST body string used in the original request; affects the hash.

### Confirmation flags

- `--yes` — skip the y/N confirmation prompt for write/delete.
- `--yes-general` — required **in addition to** `--yes` for any write/delete against `--general`.

### Defaults

- env = `prod`
- date = today, formatted `YYYYMMDD` in **local TZ** (matches `dayjs().format('YYYYMMDD')` used by `DateHelper.toDailyString()` in the codebase — NOT UTC).
- body = literal string `undefined` (matches `JSON.stringify(undefined) === "undefined"` — that's how the runtime builds the cache key for GET requests).

## Examples

```bash
# READ
ams-s3 https://www.otomoto.pl/osobowe/oferta/abc-123             # prod, today, daily cache
ams-s3 ee315ac12567a2b44ae03fc30b093334                          # prod store-vehicle
ams-s3 stage ee315ac12567a2b44ae03fc30b093334 --dealer           # stage store-dealer
ams-s3 prod https://www.otomoto.pl/abc --date=20260518           # daily cache from a past day
ams-s3 prod https://api.example.com/listings \
       --body='{"page":1,"brand":"BMW"}'                          # API daily cache, body matters

# WRITE (stage / local only — refused on prod)
ams-s3 stage https://www.example.com --write=./response.html     # seed today's daily cache
ams-s3 local ee315ac12567a2b44ae03fc30b093334 --write=./veh.json # seed local store
ams-s3 stage <storeId> --write=./veh.json --rent --yes           # seed rent bucket, no prompt

# DELETE (stage / local only — refused on prod)
ams-s3 stage ee315ac12567a2b44ae03fc30b093334 --delete           # delete from stage store
ams-s3 stage https://www.example.com --delete --date=20260519    # delete yesterday's cache
ams-s3 local <storeId> --delete --dealer --yes                   # delete dealer, no prompt
```

## Runbook (what to execute on every invocation)

### Step 1 — Parse args

Identify:

- **env** — first positional, if exactly `prod` / `stage` / `local`. Otherwise env = `prod` and the first positional is the input. URLs and 32-char hex storeIds never collide with the three env names.
- **action** — `read` (default), `write` (if `--write=<file>` present), `delete` (if `--delete` present). It is an error to pass both `--write` and `--delete`.
- **input** — the positional argument that is NOT the env (URL or storeId).
- **date**, **body**, **bucket flag** (`--rent` / `--dealer` / `--deleted` / `--general`), **confirmation flags**.

If no positional input → print this SKILL.md's "Help" section (the invocation table + examples) and stop.

### Step 2 — Hard guard

```
if [[ "$ENV" == "prod" && ( -n "$WRITE_FILE" || "$ACTION" == "delete" ) ]]; then
    echo "REFUSED: ams-s3 prod is read-only. Use stage or local for write/delete."
    exit 1
fi
```

Runs **immediately after** arg parsing. No credential loading, no S3 key construction. Even with `--yes` and `--yes-general` set, refuse on prod.

### Step 3 — Detect mode

- `^[a-f0-9]{32}$` → STORE mode
- `^https?://` → DAILY_CACHE mode
- `--general` flag set → GENERAL mode (key = input as-is)
- Otherwise → print "couldn't determine if your input is a storeId, URL, or general key" + help, exit.

### Step 4 — Resolve bucket

| Mode | Resolved bucket env var |
|---|---|
| DAILY_CACHE | `AMS_S3_${ENV^^}_BUCKET_DAILY_CACHE` |
| STORE (default) | `AMS_S3_${ENV^^}_BUCKET_STORE_VEHICLE` |
| STORE `--rent` | `AMS_S3_${ENV^^}_BUCKET_STORE_VEHICLE_RENT` |
| STORE `--dealer` | `AMS_S3_${ENV^^}_BUCKET_STORE_DEALER` |
| STORE `--deleted` | `AMS_S3_${ENV^^}_BUCKET_SID_DELETED_VEHICLES` |
| GENERAL | `AMS_S3_${ENV^^}_BUCKET_GENERAL_STORAGE` |

### Step 5 — Compute S3 key

```bash
# STORE mode (storeId is the input)
SID="$INPUT"
KEY="${SID:0:1}/${SID:1:1}/${SID:2:1}/${SID}"

# DAILY_CACHE mode
DATE="${DATE:-$(date '+%Y%m%d')}"   # local TZ
BODY="${BODY:-undefined}"
HASH=$(printf '%s_%s' "$URL" "$BODY" | md5 -q)   # macOS; on Linux: | md5sum | awk '{print $1}'
KEY="${DATE}/${HASH}"

# GENERAL mode
KEY="$INPUT"
```

Verify against codebase: `src/database/s3/s3.service.ts` (`generateKey`, `calculatePrefix`), `src/shared/utils/Hash.ts` (md5 hex), `src/shared/utils/Date.helper.ts` (`toDailyString` → `YYYYMMDD` via dayjs local TZ). For the daily-cache `${url}_${JSON.stringify(body)}` construction, see `src/crawler/CrawlerAbstract.ts`.

### Step 6 — Load env vars from `.env`

Read only the `AMS_S3_${ENV^^}_*` lines from `~/Projects/market-study/.env`. Strip the `AMS_S3_${ENV^^}_` prefix and re-export to a subshell scope as plain AWS vars:

```bash
ENV_UP=$(printf '%s' "$ENV" | tr '[:lower:]' '[:upper:]')
PREFIX="AMS_S3_${ENV_UP}_"

# Required vars (resolve into shell vars without leaking to parent)
declare -A V
while IFS='=' read -r k v; do
    [[ "$k" == ${PREFIX}* ]] || continue
    short="${k#$PREFIX}"
    V[$short]="$v"
done < <(grep "^${PREFIX}" ~/Projects/market-study/.env)

# Map to AWS vars for the subshell
export AWS_ACCESS_KEY_ID="${V[AWS_ACCESS_KEY_ID]:?missing ${PREFIX}AWS_ACCESS_KEY_ID in .env}"
export AWS_SECRET_ACCESS_KEY="${V[AWS_SECRET_ACCESS_KEY]:?missing ${PREFIX}AWS_SECRET_ACCESS_KEY in .env}"
export AWS_DEFAULT_REGION="${V[AWS_S3_REGION]:?missing ${PREFIX}AWS_S3_REGION in .env}"
ENDPOINT="${V[AWS_S3_ENDPOINT]:-}"   # only set for local/localstack
BUCKET="${V[$BUCKET_KEY]:?missing ${PREFIX}${BUCKET_KEY} in .env}"
```

If any required var is missing → print exactly which `AMS_S3_*` name is missing in `.env`, point at the Setup section, exit. Do NOT print the values of any var.

`ENDPOINT_FLAG`: `--endpoint-url=$ENDPOINT` if `ENDPOINT` is non-empty, otherwise empty string.

### Step 7 — Action

**READ:**

```bash
OUT_PATH="$HOME/Projects/market-study/.ams-s3-cache/${ENV}_${BUCKET_ALIAS}_${SHORTKEY}_$(date '+%Y%m%d%H%M%S').<ext>"
mkdir -p "$(dirname "$OUT_PATH")"
aws s3 cp "s3://${BUCKET}/${KEY}" "$OUT_PATH" ${ENDPOINT_FLAG}
```

Sniff the first 16 bytes to choose the extension:

- starts with `<` → `.html`
- starts with `{` or `[` (after trim) → `.json`
- else → `.txt`

Then `open "$OUT_PATH"`.

**WRITE:**

```bash
# HEAD first to see if it exists
EXISTS=$(aws s3api head-object --bucket "$BUCKET" --key "$KEY" ${ENDPOINT_FLAG} 2>/dev/null && echo "exists" || echo "new")
echo "About to WRITE $WRITE_FILE → s3://${BUCKET}/${KEY} ($EXISTS)"

# Confirm unless --yes
if [[ -z "$YES" ]]; then read -p "Proceed? (y/N) " ans; [[ "$ans" =~ ^[Yy]$ ]] || exit 1; fi

# --general requires --yes-general
if [[ "$MODE" == "GENERAL" && -z "$YES_GENERAL" ]]; then
    echo "REFUSED: write/delete against --general requires --yes-general"; exit 1
fi

# Refuse missing/empty local file
[[ -s "$WRITE_FILE" ]] || { echo "REFUSED: $WRITE_FILE is missing or empty"; exit 1; }

aws s3 cp "$WRITE_FILE" "s3://${BUCKET}/${KEY}" ${ENDPOINT_FLAG}
```

**DELETE:**

```bash
EXISTS=$(aws s3api head-object --bucket "$BUCKET" --key "$KEY" ${ENDPOINT_FLAG} 2>/dev/null && echo "exists" || echo "missing")
echo "About to DELETE s3://${BUCKET}/${KEY} ($EXISTS)"

[[ "$EXISTS" == "missing" ]] && { echo "Nothing to delete."; exit 0; }

if [[ -z "$YES" ]]; then read -p "Proceed? (y/N) " ans; [[ "$ans" =~ ^[Yy]$ ]] || exit 1; fi
if [[ "$MODE" == "GENERAL" && -z "$YES_GENERAL" ]]; then
    echo "REFUSED: write/delete against --general requires --yes-general"; exit 1
fi

aws s3 rm "s3://${BUCKET}/${KEY}" ${ENDPOINT_FLAG}
```

### Step 8 — Report

Print:

- `env`, `mode` (DAILY_CACHE / STORE / GENERAL), `bucket alias`, `S3 key` (full)
- which `AMS_S3_${ENV^^}_*` prefix was used (names only, not values)
- action taken (READ / WROTE / DELETED)
- for READ: file path, file size, opened ✓
- on 404 (`NoSuchKey`): show the constructed key + likely causes (wrong date, wrong env, body mismatch, listing already deactivated → check `--deleted`)
- on `AccessDenied`: show prefix used; suggest IAM key check

## Setup (one-time)

**Source of truth: `~/Projects/market-study/.env`.** All three blocks (LOCAL, STAGE, PROD) live there, prefixed so they don't collide with the runtime app config. The legacy `~/Projects/s3-file-fetcher-gui/.env.{prod,stage}` is no longer needed once these blocks are populated.

```bash
# === ams-s3 skill — PROD (READ-ONLY) ===
AMS_S3_PROD_AWS_ACCESS_KEY_ID=...
AMS_S3_PROD_AWS_SECRET_ACCESS_KEY=...
AMS_S3_PROD_AWS_S3_REGION=...
AMS_S3_PROD_BUCKET_DAILY_CACHE=...
AMS_S3_PROD_BUCKET_STORE_VEHICLE=...
AMS_S3_PROD_BUCKET_STORE_VEHICLE_RENT=...
AMS_S3_PROD_BUCKET_STORE_DEALER=...
AMS_S3_PROD_BUCKET_SID_DELETED_VEHICLES=...
AMS_S3_PROD_BUCKET_GENERAL_STORAGE=...

# === ams-s3 skill — STAGE (read/write/delete) ===
AMS_S3_STAGE_AWS_ACCESS_KEY_ID=...
AMS_S3_STAGE_AWS_SECRET_ACCESS_KEY=...
AMS_S3_STAGE_AWS_S3_REGION=...
AMS_S3_STAGE_BUCKET_DAILY_CACHE=...
AMS_S3_STAGE_BUCKET_STORE_VEHICLE=...
AMS_S3_STAGE_BUCKET_STORE_VEHICLE_RENT=...
AMS_S3_STAGE_BUCKET_STORE_DEALER=...
AMS_S3_STAGE_BUCKET_SID_DELETED_VEHICLES=...
AMS_S3_STAGE_BUCKET_GENERAL_STORAGE=...

# === ams-s3 skill — LOCAL (read/write/delete; localstack OR personal bucket) ===
AMS_S3_LOCAL_AWS_ACCESS_KEY_ID=...
AMS_S3_LOCAL_AWS_SECRET_ACCESS_KEY=...
AMS_S3_LOCAL_AWS_S3_REGION=us-east-1
AMS_S3_LOCAL_AWS_S3_ENDPOINT=http://localhost:<port>     # localstack only — omit when using a real personal bucket
AMS_S3_LOCAL_BUCKET_DAILY_CACHE=...
AMS_S3_LOCAL_BUCKET_STORE_VEHICLE=...
AMS_S3_LOCAL_BUCKET_STORE_VEHICLE_RENT=...
AMS_S3_LOCAL_BUCKET_STORE_DEALER=...
AMS_S3_LOCAL_BUCKET_SID_DELETED_VEHICLES=...
AMS_S3_LOCAL_BUCKET_GENERAL_STORAGE=...
```

Also add to `~/Projects/market-study/.gitignore` (if not already):

```
.ams-s3-cache/
```

**IAM recommendation:** the prod credentials (`AMS_S3_PROD_AWS_*`) should belong to a **read-only** IAM key. The skill's hard refusal is the primary guard, but a read-only key catches the case where the guard is bypassed by accident.

## What the skill does NOT do

- Does **not** write or delete on prod (hard refusal).
- Does **not** fetch live URLs (S3 cached snapshots only).
- Does **not** validate data quality — use `crawler-data-validation` for that.
- Does **not** list or search S3 keys — given a key, fetches/writes/deletes it.
- Does **not** write or delete against `--general` without `--yes-general`.
- Does **not** modify any file outside `~/Projects/market-study/.ams-s3-cache/` and the explicitly-named `--write` target.
- Does **not** print AWS key values.

## Cross-references (other skills that use this one)

- `crawler-debug` — inspect raw S3 responses and stored vehicle JSON during a failure investigation.
- `crawler-data-validation` — fetch the original S3 doc next to the ES hit for field-level checks.

## Future evolution

This skill is **instruction-only** (no persisted script). The runbook above is what Claude executes step-by-step using Bash. The trade-off: simpler to maintain and modify, more tokens per invocation than a compiled script.

**If invocation cost becomes a concern** (lots of repeated calls from chained flows like `crawler-debug` and `crawler-data-validation`), migrate the runbook into a TypeScript script at `scripts/ams-s3.ts` invoked as `npx ts-node scripts/ams-s3.ts ...`. Expected token reduction per call: ~80%, since the runbook collapses into a single Bash invocation and the script handles all branching internally. The SKILL.md then becomes a one-paragraph wrapper that delegates everything.
