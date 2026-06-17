# JS / TS Code Standards

Two-part doc:
1. **Part 1 — General JS/TS baseline** (Confluence baseline). Most is Prettier/ESLint-enforced; key project values: 4-space indent, 240-char lines, single quotes, trailing commas, explicit return types, no `any`, `===` only, no default exports, no `// @ts-ignore`, no async logic in constructors, path aliases only (never `../../..`).
2. **Part 2 — Project-specific patterns** (harvested from sessions): logger structure, error-handling tiers, DTO validators, Cheerio selectors, naming, control flow, tests, and more.

**Re-check Part 2 before committing changed files.** Run `ams-save` at end of session to harvest new findings. Crawler error-handling tiers and the retry-loop model live in [foundational.md](~/Projects/market-study-knowledge/foundational.md).

---

## Part 1 — General JS/TS standards (Confluence baseline)

**Source:** https://preskok.atlassian.net/wiki/spaces/TT/pages/2489877034/JS+and+TS+Standards

### Foundation
- **airbnb/base** is the default style guide. Per-framework or per-project rules override it.
- ESLint config extends `airbnb/base` and/or `airbnb/recommended`. Prefer `.eslintrc.js` so rules can be commented.
- Prettier is the formatter. When ESLint and Prettier disagree, conform to Prettier.

### Code quality
- **Remove `console.log` and dead/commented code** before commit — git history exists for a reason.
- **Avoid early returns** as an escape hatch. Push checks up to the caller. Exceptions: framework patterns (React `useEffect`), abstract util functions.
- **Avoid long optional-chaining chains** (`a?.b?.c?.d`). Split into named intermediate variables — easier to debug, document, and short-circuit.
- **`null` not `undefined`** for explicit "no value" cases. `undefined` is only for optional params and 3rd-party returns.
- **Always assign a default** to declared variables. Never leave them uninitialised.
- **Declarative over imperative** (`.map`, `.filter`) — but split chained calls into named chunks for debuggability. Avoid `.map().filter().sort().reduce()` one-liners.
- **Destructure only the top level** of API responses. Drill into deeper levels with explicit checks.
- **Use parameter destructuring** when a function has > 2 params. Define an interface for the params object.
- **Default arguments over short-circuit** (`count = 10` not `count !== undefined ? count : 10`).
- **No empty catch blocks.** Either log, throw a custom error, or return a default — and add a comment if it's a deliberate silent fallthrough.
- **Avoid side effects** — pure functions whenever possible. No mutating globals or shared objects.
- **`async/await` over `.then()` chains.**
- **Strict equality (`===`) only.** Failing this is a breaking change in review.
- **Searchable names.** Magic numbers extracted into named constants (`MILLISECONDS_PER_DAY = 24 * 60 * 60 * 1000`).
- **Explicit return types on all functions** — even when TS can infer. Forces a sanity check.
- **Docblocks** above non-trivial functions.
- **Consistent vocabulary** for the same concept (`getUser`, not a mix of `getUserInfo` / `getUserDetails` / `getUserData`).
- **No flags as function params.** A boolean flag almost always means the function is doing two things — split it.
- **Arrow functions** preferred for functional code; named function declarations OK for OOP/debugging.

### TypeScript
- Minimum tsconfig: `strict`, `noImplicitAny`, `strictNullChecks`, `noImplicitReturns`, `allowSyntheticDefaultImports`, `esModuleInterop`, `experimentalDecorators`, `emitDecoratorMetadata`.
- **`prop?: T | null`** when the key may be omitted entirely (opt-in field).
- **`prop: T | null | undefined`** when the key must always be present but the value may be absent (strict contract).
- **Domain-driven types:** use `Pick<DomainObject, 'field'>` instead of repeating primitives. Changes to the domain object then cascade.
- **Inline types** are fine for one-off usage. Promote to a standalone type/interface only when reused.
- **No `export` on a type/interface used only within its own module.** Signals "not for reuse".
- Suffix convention: `Enum`, `Type` (singular). `ToggleEnum`, `UserStatusType`.
- `string[]` vs `Array<string>`: pick one per scope, don't mix.
- Folder names: lowercase, kebab-case. File names: `[domain].[type].[ext]` (e.g. `account.helper.ts`).

---

## Part 2 — Project-specific patterns (harvested from sessions)

Each entry: rule + example + source. No prose.

### Logger call — opening brace on same line, each field on its own line

```typescript
// .log() / .warn() — object then context on same closing line
this.logger.warn({
    message: 'Short description',
    site,
    vehicleUrl: vehicle.url,
}, LoggingContexts.DATA_FIX);

// .error() — object then stack + context on same closing line
this.logger.error({
    message: 'Short description',
    site,
    errorMessage: ex.message,
}, ex.stack, LoggingContexts.DATA_FIX);
```

Rules:
- Opening `{` on the same line as the logger call — never `this.logger.error(\n    {`
- Each field on its own line inside the object
- Closing `},` followed by remaining args on the same line
- `message` is always the first key
- `.error()` second arg is stack, third is context; `.log()` / `.warn()` second arg is context
- Never compress all fields into a single inline object: `{ message: '...', site, errorMessage: ex.message }` on one line is wrong

**Source:** session 2026-05-20, corrected format 2026-06-08.

### Logging context — most specific enum

`active-vehicle.*` operations → `ACTIVE_VEHICLES`. Generic controller error paths → `ROUTE_CONTROLLER`. New context enum needs ES-schema buy-in.

**Source:** session 2026-05-20.

### Descriptive variable names — Redis round-trip convention

```typescript
const deactivatedSitesRaw = await redis.read(...);                  // raw JSON string
const deactivatedSites = JSON.parse(deactivatedSitesRaw);           // parsed
const deactivatedSitesStringified = JSON.stringify(deactivatedSites); // back to string
```

No `existing` / `data` / `updated` / `serialised` / `result`. Name the entity. Suffix pattern: `<noun>Raw` / `<noun>` / `<noun>Stringified`.

**Source:** session 2026-05-20.

### Positive-flow `if` — match over `continue`

```typescript
// preferred
for (const x of xs) {
    if (cond) {
        doWork(x);
    }
}
```

Reach for `continue` only with multiple stacked skip conditions.

**Source:** session 2026-05-20.

### Persisted timestamps — ISO string, not epoch

```typescript
timestamp: DateHelper.toISOString({}),   // "2026-05-20T10:30:00.000Z"
```

Use string form for anything stored in Redis/MySQL/S3. `Date.now()` only for ephemeral RMQ payload `date` fields.

**Source:** session 2026-05-20.

### DTO required boolean — `@IsBoolean()` alone is sufficient

```typescript
// GOOD — @IsDefined() is redundant, @IsBoolean() already rejects undefined and null
@IsBoolean()
iConfirm: boolean;

// BAD — @IsDefined() adds nothing here
@IsDefined()
@IsBoolean()
iConfirm: boolean;
```

`@IsBoolean()` already rejects `undefined` and `null`. Do not stack `@IsDefined()` on top of it.

**Source:** session 2026-05-20, corrected 2026-05-25.

### DTO string field — `@IsString()` allows empty string

```typescript
// GOOD — rejects empty string
@IsString()
@IsNotEmpty()
reason: string;

// BAD — accepts "" silently
@IsString()
reason: string;
```

`@IsString()` accepts `""`. Add `@IsNotEmpty()` whenever an empty string is not a valid value.

**Source:** session 2026-05-25.

### Business logic in services, not controllers

Controller: DTO validate → call one service method → catch, log, throw `BadRequestException`. Redis reads/writes, key composition, entry construction → service.

**Source:** session 2026-05-20.

### Use imported types explicitly

```typescript
const entry: DeactivationPreventedSiteEntry = { timestamp, reason };
deactivatedSites[site] = entry;
```

No stale type imports — bind them to a typed constant.

**Source:** session 2026-05-20.

### `satisfies <NamedInterface>` over inline shape

```typescript
// interface file
export interface DeactivationPreventionThresholdsConfig {
    global: number;
    perSite: Partial<Record<AvailableAdSiteKeysEnum, number>>;
}

// const file
export const DeactivationPreventionThresholds = {
    global: 0.2,
    perSite: { [AvailableAdSiteKeysEnum.AUTOBAZAR]: 0.25 },
} as const satisfies DeactivationPreventionThresholdsConfig;
```

**Source:** session 2026-05-20.

### No try/catch around Redis JSON round-trips

`JSON.stringify` on a Redis-sourced object can't fail meaningfully. Don't wrap it. Same for `JSON.parse` when we own all writers.

**Source:** session 2026-05-20.

### Imports — path aliases only

`@vehicle/...`, `@shared/...`, `@database/...` or node_module. Never `../../../`. Sorted by `simple-import-sort` (enforced).

**Source:** session 2026-05-20.

### Repository per entity, not per consumer

`active-vehicles.repository.ts` holds every method touching `VehicleVisitEntity`, regardless of which cron/feature calls it.

**Source:** session 2026-05-20.

### `DateHelper` over raw `Date`

```typescript
DateHelper.toFormattedString({ format: 'YYYY-MM-DD' });   // not new Date().toISOString().split('T')[0]
DateHelper.toISOString({});                                // not Date.now()
DateHelper.isBefore({ conditionDate });                    // not d < other
```

**Source:** session 2026-05-20.

### Distinguishable endpoint names

If two endpoints share a verb in the same controller, rename one. `prevent-deactivation` collided with `check-and-prevent-deactivation` → renamed to `lock-site-deactivation` / `unlock-site-deactivation`.

**Source:** session 2026-05-20.

### Trust the DTO — no fallback for required fields

```typescript
// DTO requires `reason`
deactivatedSites[site] = { timestamp, reason };   // no `reason || 'manual lock'`
```

**Source:** session 2026-05-20.

### Comment non-obvious spreads/preserves

```typescript
// spread existing locked sites so they are preserved in Redis when we write back
const updatedPreventedSites: DeactivationPreventedSites = { ...deactivatedSites };
```

**Source:** session 2026-05-20.

### Crawler-prefix rule for interfaces in site interface files

Exported interfaces use the crawler name as prefix. Non-exported (file-private) interfaces used only within the same interface file do NOT get the crawler prefix.

```typescript
// BAD - non-exported sub-interfaces carry the crawler prefix
export interface MobileInitialState { shared?: MobileInitialStateShared; }
interface MobileInitialStateShared { referenceData?: MobileInitialStateReferenceData; }

// GOOD
export interface MobileInitialState { shared?: InitialStateShared; }
interface InitialStateShared { referenceData?: InitialStateReferenceData; }
```

**Source:** session 2026-06-17 (MAR-2067 mobile.de).

### Extract repeated inline object types to named interfaces

When `Array<{ site: string; ratio: number }>` appears on two or more signatures, extract to the domain interface file (e.g. `DeactivationPreventedSite.interface.ts`).

```typescript
// BAD — repeated inline shape
private evaluateSiteLocks(...): { ...; newlyLocked: Array<{ site: string; ratio: number }> } | null {}
private notifyLockedSites(newlyLocked: Array<{ site: string; ratio: number }>, ...): Promise<void> {}

// GOOD
export interface SiteLockEntry { site: string; ratio: number; }
private evaluateSiteLocks(...): { ...; newlyLocked: Array<SiteLockEntry> } | null {}
private notifyLockedSites(newlyLocked: Array<SiteLockEntry>, ...): Promise<void> {}
```

**Source:** session 2026-05-20.

### Destructure static helpers to avoid repetition

When calling the same static method multiple times in one block, destructure it once.

```typescript
// BAD
lines.push(`locked at: ${DateHelper.toFormattedString({ date: ts1, format })}`);
lines.push(`locked since: ${DateHelper.toFormattedString({ date: ts2, format })}`);

// GOOD
const { toFormattedString } = DateHelper;
lines.push(`locked at: ${toFormattedString({ date: ts1, format })}`);
lines.push(`locked since: ${toFormattedString({ date: ts2, format })}`);
```

**Source:** session 2026-05-20.

### Guard early-return belongs inside the method, not at the call site

Move `if (empty) return` guards to the top of the called method. The caller should not need to know the method is a no-op on empty input.

```typescript
// BAD — caller guards
if (Object.keys(allLockedSites).length > 0) {
    await this.notifyLockedSites(newlyLocked, allLockedSites);
}

// GOOD — guard inside method
private async notifyLockedSites(...): Promise<void> {
    if (Object.keys(allLockedSites).length === 0) return;
    ...
}
```

**Source:** session 2026-05-20.

### Method naming — `evaluate/detect/compute` for pure calculations, not `build/update`

`build` and `update` imply a side effect (writing state). Methods that only compute and return data should use `evaluate`, `detect`, `compute`, or `resolve`.

```typescript
// BAD — implies Redis write happens inside
private buildUpdatedPreventedSites(...) {}

// GOOD — signals pure evaluation, caller does the write
private evaluateSiteLocks(...) {}
```

**Source:** session 2026-05-20.

### Unify conditional data before a single call — avoid multiple conditional call sites

When the same method would be called from two branches with different arguments, unify the arguments first and call once.

```typescript
// BAD — two call sites
if (!lockResult) {
    if (Object.keys(deactivatedSites).length > 0) await this.notifyLockedSites([], deactivatedSites);
    return;
}
await this.notifyLockedSites(lockResult.newlyLocked, lockResult.updatedPreventedSites);

// GOOD — one call site
const newlyLocked = lockResult?.newlyLocked ?? [];
const allLockedSites = lockResult?.updatedPreventedSites ?? deactivatedSites;
if (lockResult) { await this.redisService.write(...); }
await this.notifyLockedSites(newlyLocked, allLockedSites);
```

**Source:** session 2026-05-20.

### scrape.do — always test 1-credit tier before assuming super is needed

Default to `superAtRetry: null` (1 credit/request, datacenter proxies). Only escalate to `superAtRetry: 0` (10 credits, residential) if 1cr returns 502 RotationFailed or consistent 403s. Many CF-protected endpoints that seem blocked pass through on 1cr.

```typescript
// DEFAULT — start cheap, escalate only if needed
private readonly scrapeDoProxyConfig: ScrapeDoProxyConfig = {
    superAtRetry: null,       // 1 credit, datacenter
    superBrowserAtRetry: null,
};

// Only if 1cr fails consistently:
private readonly scrapeDoProxyConfig: ScrapeDoProxyConfig = {
    superAtRetry: 0,          // 10 credits, residential from first retry
    superBrowserAtRetry: null,
};
```

**Source:** session 2026-06-01 (auto-connect — assumed super needed, 1cr worked fine).

### DTO confirmation flag — `@IsIn([true])`, drop the controller guard

```typescript
// DTO — literal true is the only valid value
@IsIn([true])
iConfirm: true;
```
```typescript
// controller — NO manual guard needed; class-validator rejects false/undefined
// with a descriptive error logged at the interceptor level
async lockSiteDeactivation(@Body() body: LockDeactivationForSiteDto): Promise<void> {
    return this.service.lock(body.site, body.reason);
}
```

For an explicit opt-in flag, `@IsIn([true])` (typed `iConfirm: true`) is stricter than `@IsBoolean()` and removes the `if (!body.iConfirm) throw new BadRequestException(...)` guard from the controller.

**Source:** session 2026-06-02.

### DTO inheritance for shared fields

```typescript
export class UnlockDeactivationForSiteDto {
    @IsEnum(AvailableAdSiteKeysEnum)
    site: AvailableAdSiteKeysEnum;

    @IsIn([true])
    iConfirm: true;
}

export class LockDeactivationForSiteDto extends UnlockDeactivationForSiteDto {
    @IsString()
    @IsNotEmpty()
    reason: string;
}
```

Two DTOs sharing fields go in one file; the larger one `extends` the smaller. No duplicated validators.

**Source:** session 2026-06-02.

### One interface file per domain — `<Domain>.interface.ts`

All interfaces/types for one service domain live in a single `<Domain>.interface.ts` (e.g. `ActiveVehicle.interface.ts`), not file-per-interface. If an interface is used only where a const is defined, inline it there instead of a separate file.

**Source:** session 2026-06-02.

### Reuse existing Graylog log fields — don't introduce new ones

```typescript
// GOOD — reuse errorMessage (existing text field in Graylog)
this.logger.warn({ message: 'Deactivation LOCKED for site', site, errorMessage: reason }, LoggingContexts.ACTIVE_VEHICLES);

// BAD — new field name needs ES schema buy-in, costs retention
this.logger.warn({ message: '...', site, ratioPercent: 42 }, ...);
```

Graylog ES is shared across projects with ~7-day retention. Reuse `errorMessage` (safe text field) for ad-hoc context rather than adding new field names. Prefer one log line per `site` so it filters cleanly on the `site` field.

**Source:** session 2026-06-02.

### `DataHelper.normalizeNumericValue` over `parseInt` for raw SQL strings

```typescript
// GOOD
todayCount: DataHelper.normalizeNumericValue(row.todayCount),

// BAD
todayCount: parseInt(row.todayCount) || 0,
```

Raw query results (`getRawMany`) return numeric columns as strings — convert with `DataHelper.normalizeNumericValue`, not `parseInt`. (`SUM()`/`COUNT()` on a non-empty GROUP never returns null, so no `|| 0` fallback needed.)

**Source:** session 2026-06-02.

### Destructure params — don't pass a default just to reach a later arg

```typescript
// GOOD — object params, caller omits defaults
public async getVehiclesBeforeDate({ beforeDate, limit = 1000, excludeSites = [] }: { beforeDate: Date, limit?: number, excludeSites?: Array<RunnableAdSiteKey> }): Promise<...> {}
// caller:
await repo.getVehiclesBeforeDate({ beforeDate, excludeSites });

// BAD — forced to pass the default 1000 positionally to reach excludeSites
await repo.getVehiclesBeforeDate(beforeDate, 1000, excludeSites);
```

When a method's optional middle param has a default and a caller only needs a later param, switch to a destructured object param. See JS+TS Standards § Parameters destructuring.

**Source:** session 2026-06-02.

### No-op guard — use if/else, not early return

For a branch that does nothing (no-op), use `if/else` rather than an early `return`.

```typescript
// GOOD
if (deactivatedSites[site]) {
    this.logger.log({ message: 'Already locked — skipping', site }, ctx);
} else {
    // ... do the work ...
}

// BAD
if (deactivatedSites[site]) {
    this.logger.log({ message: 'Already locked — skipping', site }, ctx);
    return;
}
// ... do the work ...
```

**Source:** session 2026-06-03.

### Extract complex threshold / decision logic to a named private method

When a service method needs to resolve a value through multi-step branching (e.g. priority chain, group lookup), extract to `private get<Noun>(arg): Type` with a docblock. Keep the calling method clean.

```typescript
// In evaluateSiteLocks — clean call site
const threshold = this.getSiteThreshold(site);

// Dedicated method — all the branching lives here
/**
 * Resolves the deactivation prevention threshold for a site.
 * Priority: perSite override → site size + crawl frequency.
 */
private getSiteThreshold(site: RunnableAdSiteKey): number {
    const isNthDayCrawler = !!CrawlingSites[site].runOnNthDays;
    const crawlerType = isNthDayCrawler ? 'nthDay' : 'daily';
    const siteGroup = SiteThresholds[site] === 0.1
        ? DeactivationPreventionThresholds.largeSite
        : DeactivationPreventionThresholds.smallSite;
    return DeactivationPreventionThresholds.perSite[site] ?? siteGroup[crawlerType];
}
```

**Source:** session 2026-06-03.

### New methods go at the end of the service file

Existing (pre-ticket) methods stay at the top. All methods added in a PR go below them — never interspersed. Keeps diffs clean and reviewers focused on what changed.

**Source:** session 2026-06-03 (mlencek PR #21).

### Re-throw exceptions that should be retried by the scheduler

```typescript
// GOOD — HTTP 500 triggers cron retry
} catch (ex) {
    this.logger.error({ message: '...', errorMessage: ex.message }, ex.stack, ctx);
    throw ex; // re-throw so external scheduler can retry
}

// BAD — silent return masks failure, cron thinks it succeeded
} catch (ex) {
    this.logger.error({ message: '...' }, ex.stack, ctx);
    return;
}
```

Add a comment explaining WHY the throw is there — it's not the usual pattern and reviewers will question it.

**Source:** session 2026-06-03 (mlencek PR #21).

### Don't guard against impossible cases

Remove optional chaining (`?.`), null checks, or fallback values when the type or flow guarantees the value exists. Defensive code that can never fire misleads readers into thinking the case is possible.

```typescript
// BAD — site is always a key of preventedSites, ?.reason is impossible to be undefined
errorMessage: preventedSites[site]?.reason,

// GOOD
errorMessage: preventedSites[site].reason,
```

**Source:** session 2026-06-03 (mlencek PR #21).

### Don't commit development artifacts in PRs

`.gitignore` entries for personal tooling (IDE files, Claude state, local knowledge base) should be handled via IDE's own ignore settings — not committed to the repo. Similarly, `.http` test requests for endpoints that are dangerous to call manually (e.g. `check-and-prevent-deactivation`) should not be in committed `.http` files.

A `pre-push` hook in `.git/hooks/pre-push` automatically reverts all `*.http` files to their `develop` state before pushing, so local test modifications are never pushed. Commits to `.http` files are allowed (intentional changes go through normally); the hook only fires if the branch tip differs from `develop`.

**Source:** session 2026-06-03 (mlencek PR #21).

### Prefer CrawlingSites config over MySQL for site configuration

```typescript
// GOOD — live config, always up to date
const isNthDayCrawler = !!CrawlingSites[site].runOnNthDays;

// BAD — stale; insertOrUpdate doesn't update runOnNthDays column
const isNthDayCrawler = !!vehicleVisitEntity.runOnNthDays;
```

`runOnNthDays` in `vehicle_visit` is only set on INSERT, not updated on re-crawl. CrawlingSites config reflects current intent.

**Source:** session 2026-06-03 (mlencek PR #21).

### Exception variable — always `ex`, never `e`/`err`/`error`

```typescript
// GOOD
} catch (ex) {
    this.logger.error({ message: ex.message }, ex.stack, ctx);
}

// BAD
} catch (e) { ... }
} catch (err) { ... }
} catch (error) { ... }
```

**Source:** session 2026-06-03 (mlencek PR #21).

### Service timing — `const start = Date.now()` + `durationMilliseconds` in finish log

Every public service method that does meaningful work starts a timer and logs it on finish. Use existing numeric fields where possible.

```typescript
public async doWork(): Promise<void> {
    const start = Date.now();
    this.logger.log({ message: 'Starting ...' }, ctx);

    // ... work ...

    this.logger.log({
        message: 'Finished ...',
        count: itemsProcessed,
        durationMilliseconds: Date.now() - start,
    }, ctx);
}
```

**Source:** session 2026-06-03 (mlencek PR #21, also `store-vehicle.service.ts`, `deleted-data-vehicle.service.ts`).

### Don't pass a param that will always be today's date

If a method parameter is always today's date (or any constant derived from `Date.now()`), compute it inside the method. Accepting it as a param implies callers might pass a different value, creating false API surface.

```typescript
// BAD — todayDateStr is always today, param implies flexibility that doesn't exist
public calculateRatios(rows: Array<Row>, todayDateStr: string): Result {}

// GOOD — compute inside
public calculateRatios(rows: Array<Row>): Result {
    const today = DateHelper.toFormattedString({ format: 'YYYY-MM-DD' });
}
```

**Source:** session 2026-06-03 (mlencek PR #21).

### Timestamp storage — use `DateHelper.toISOString`, don't format as UTC string

```typescript
// GOOD — consistent with rest of codebase Redis values
timestamp: DateHelper.toISOString({}),

// BAD — UTC string format is inconsistent with how timestamps are stored elsewhere
const format = 'YYYY-MM-DD HH:mm:ss [UTC]';
toFormattedString({ date: entry.timestamp, format })
```

The rest of the codebase does not work in UTC explicitly. Adding UTC-formatted strings only in one place is confusing to readers of Redis or email output.

**Source:** session 2026-06-03 (mlencek PR #21).

### Alert email subjects must be immediately distinguishable

Subjects that are nearly identical (differing only by an emoji) are easy to overlook in inbox filtering. Critical alerts (like deactivation locks) need unique, action-oriented subjects.

```typescript
// BAD — differ only by ⚠️ emoji, easy to miss
'⚠️ Deactivation prevention: 2 new site(s) locked (5 total)'
'Deactivation prevention: 5 site(s) currently locked'

// GOOD — "NEW" in subject makes it scannable and filterable
'⚠️ Alert: 2 NEW site(s) locked deactivation'
```

**Source:** session 2026-06-03 (mlencek PR #21).

### No try/catch around email sends unless there's a real failure mode

```typescript
// BAD — not done elsewhere, adds noise, hides that errors propagate normally
try {
    await this.commonEmailsService.sendReportingEmail({ ... });
} catch (emailEx) { ... }

// GOOD — let it propagate; if email fails the caller sees it
await this.commonEmailsService.sendReportingEmail({ ... });
```

**Source:** session 2026-06-03 (mlencek PR #21).

### Make `dateField`-style options required — no silent defaults

When a method is called from multiple places with different semantics (e.g. one caller needs `activeFrom`, another needs `createdAt`), make the option required with no default. Forces every caller to be explicit and prevents silent mismatches.

```typescript
// BAD — default hides intent, callers silently get wrong behaviour
public async getVehiclesBySiteAndDate({
    dateField = 'activeFrom',
}: ... & { dateField?: 'activeFrom' | 'createdAt' })

// GOOD — required, every caller documents its intent
public async getVehiclesBySiteAndDate({
    dateField,
}: ... & { dateField: 'activeFrom' | 'createdAt' })
```

**Source:** session 2026-06-04 (MAR-1975 — export uses createdAt, URL-fix uses activeFrom).

### Vehicles read from the Data index are already mapped — use saveVehiclesToDataIndex

Vehicles fetched from the ES Data index (`DataAdVehicle`) have already been through the Data API mapping pipeline. Sending them to `sendVehicleInputsForDataMapping` again is unnecessary and uses a channel (`DATA_SEND_JOBS`) not open in WORKER mode. Use `saveVehiclesToDataIndex` instead (sends to `MS_SEND_BULK_SAVE_JOBS`, open in WORKER).

```typescript
// BAD — re-maps already-mapped vehicles, wrong channel for WORKER mode
await this.crawlerMessagesRoutingService.sendVehicleInputsForDataMapping(vehicles);

// GOOD — vehicles from Data index are already mapped
await this.crawlerMessagesRoutingService.saveVehiclesToDataIndex(vehicles);
```

**Source:** session 2026-06-04 (MAR-1975 update-vehicle-urls service).

### No em dashes in code comments — use plain hyphens

Use `-` in inline comments and docblocks. Em dashes (`—`) are not standard code style and stand out as AI-generated.

```typescript
// BAD
// recalculate deletes activeTo from inputs — restore original if needed

// GOOD
// recalculate deletes activeTo from inputs - restore original if needed
```

**Source:** session 2026-06-08 (MAR-1975 - user rejected em dashes as "sign of claude work").

### Cheerio — CSS attribute selector over JS `.filter()` callback

Use a CSS attribute selector directly instead of `.filter((_, el) => ...)` when filtering by a known attribute value. Cheerio handles it natively and it avoids O(M×N) JS-level iteration.

```typescript
// BAD
const modelOptions = loadedHtml('option').filter((_, el) => loadedHtml(el).attr('data-brand-id') === brandId);

// GOOD
const modelOptions = loadedHtml(`option[data-brand-id="${brandId}"]`);
```

Only safe when the interpolated value is guaranteed numeric/non-injectable (e.g. from a page's `option[value]` attribute). If the value comes from user input or an untrusted source, use `.filter()` instead.

**Source:** session 2026-06-15 (MAR-2101 - PR reviewer comment, applied to autobazar getBrandsAndModels).

### Cheerio — filter empty values at selector level, not with a `continue` guard

Exclude empty-value elements directly in the CSS selector using `[value]:not([value=""])` rather than selecting all then skipping inside the loop. Mirrors how brand selectors already use `option:not([value=""])`.

```typescript
// BAD
const models = loaded('input[name*="[model][]"]').toArray();
for (const model of models) {
    const modelName = loaded(model).attr('value');
    if (!modelName) continue; // guard after the fact
    // ...
}

// GOOD
const models = loaded('input[name*="[model][]"][value]:not([value=""])').toArray();
for (const model of models) {
    const modelName = loaded(model).attr('value') as string; // guaranteed non-empty by selector
    // ...
}
```

**Source:** session 2026-06-16 (MAR-2039 brueggemann — Gemini code assist suggestion, accepted by user).

### Cheerio — `[name*="segment"]` contains selector for dynamic form IDs

When a site's `name` attribute includes a dynamic segment (e.g. `search[_cs-fs-form-4704][make][]`), use the CSS attribute contains operator `*=` rather than an exact match. Exact match silently returns 0 elements if the form ID changes.

```typescript
// BAD — breaks when form ID is dynamic
const brands = loaded('select[name="search[make][]"] option:not([value=""])').toArray();

// GOOD — survives form ID rotation
const brands = loaded('select[name*="[make][]"] option:not([value=""])').toArray();
const models = loaded('input[name*="[model][]"][value]:not([value=""])').toArray();
```

**Source:** session 2026-06-16 (MAR-2039 brueggemann — brand/model selector stopped matching after site added dynamic form ID prefix).

### OtherBrandValues / OtherModelValues — register in constants, let abstract handle it

When a site has "other brand" / "other model" catch-all options, register them in `AdCrawlingSitesOtherBrandValues` / `AdCrawlingSitesOtherModelValues` in `OtherBrandAndModelsValues.ts`. Do NOT add `CrawlerHelper.isModelUnknown()` / `isBrandUnknown()` guards inside `getBrandsAndModels()` — the abstract handles those downstream automatically.

```typescript
// BAD - manual guard inside getBrandsAndModels
if (CrawlerHelper.isModelUnknown(modelName, this.site)) {
    continue;
}

// GOOD - just register in the constants file
export const AdCrawlingSitesOtherModelValues = {
    autobazar: ['iný model'],
    // ...
};
```

**Source:** session 2026-06-15 (MAR-2101 - user correction).

### JSON.parse — always guard against null literal

`JSON.parse("null")` returns JS `null` (valid JSON). Any downstream call like `Object.values()` or `.forEach()` on the result will throw. Add `?? {}` or `?? []` after every `JSON.parse` where the source string might be the literal `"null"`.

```typescript
// BAD
const equipmentObj: Record<string, Foo> = JSON.parse(equipmentJson);
Object.values(equipmentObj).forEach(...); // throws if equipmentJson === "null"

// GOOD
const equipmentObj: Record<string, Foo> = JSON.parse(equipmentJson) ?? {};
Object.values(equipmentObj).forEach(...); // safe
```

**Source:** session 2026-06-16 (MAR-2016 auto-ici — ng-init lines[2] is `"null"` when vehicle has no serial equipment).

### Split on `\n` to extract single-line JSON embedded in HTML

When extracting a `window.__INITIAL_STATE__ = ...` (or similar) assignment from HTML, split on `\n` and take index `[0]`. `JSON.stringify` always produces a single line — the first newline is always the correct end-of-JSON boundary. Do NOT rely on `;\n`, `</script>`, or `;` as delimiters; modern SSR pages regularly omit semicolons between variable declarations.

```typescript
// BAD — fails if no semicolons between window.* declarations (mobile.de)
const jsonStr = html?.split('window.__INITIAL_STATE__ = ')[1]?.split(/;\r?\n/)[0];

// GOOD — JSON.stringify output is always single-line; first \n is the boundary
const jsonStr = html?.split('window.__INITIAL_STATE__ = ')[1]?.split('\n')[0]?.trimEnd();
```

**Source:** session 2026-06-16 (MAR-2067 mobile.de — homepage HTML uses `\n` with no semicolons between `window.__INITIAL_STATE__` and `window.__PUBLIC_CONFIG__`).

### `errorInsteadOfContinue: false` means `fetchRequest` returns `undefined`, not throws

When `fetchRequestOptions` has `errorInsteadOfContinue: false`, a failed HTTP request returns `undefined` instead of throwing. `.catch(() => null)` chained on such a call is dead code — the promise never rejects.

```typescript
// BAD — .catch is dead code; fetchRequest with errorInsteadOfContinue: false never rejects
const html = await this.fetchRequest(url, this.fetchRequestOptions).catch(() => null);

// GOOD
const html = await this.fetchRequest(url, this.fetchRequestOptions);
// html is undefined on failure; handle with optional chaining downstream
const afterState = html?.split('window.__INITIAL_STATE__ = ')[1];
```

**Source:** session 2026-06-16 (MAR-2067 mobile.de `fetchMakes()`).

### Project formatter / lint config (the values Prettier + ESLint enforce)

4-space indent, 240-char lines, single quotes, trailing commas always. Plus rules not all auto-fixable: **no default exports**, **no `// @ts-ignore`** (fix the type), **no async logic in constructors** (DI only — use lifecycle hooks for async setup), async arrow has a space before `=>` (named/anonymous functions don't). Path aliases only (see "Imports — path aliases only").

**Source:** session 2026-06-17 (moved from CLAUDE.md).

### Linting — only changed files, never the whole repo

`npm run lint` runs `prettier + eslint --fix` across the **entire** codebase (400+ files) and produces massive unrelated diffs. Never run it. Lint only files you actually touched; always lint new files before their first commit.

```bash
npx prettier --write src/path/to/file.ts
npx eslint src/path/to/file.ts --fix
npx tsc --noEmit   # type-check without writes
```

**Source:** session 2026-06-17 (moved from CLAUDE.md).

### Don't mask errors with truthy defaults

Returning `[]` from `getBrandsAndModels()` on error makes the alert system think the site is legitimately empty. Throw and let the retry loop / DL handle it. (Matea's rule.) See also "Re-throw exceptions that should be retried by the scheduler".

```typescript
// BAD - swallows a real failure as "no vehicles"
catch (ex) { return []; }
// GOOD - let it propagate
catch (ex) { throw ex; }
```

**Source:** session 2026-06-17 (moved from CLAUDE.md).

### Defensive fetch — coalesce to empty string before cheerio

`cheerio.load()` throws on `undefined`. Coalesce the fetch result so the parser degrades gracefully instead of crashing.

```typescript
const html = await this.fetchRequest(url) ?? '';
const $ = cheerio.load(html);
```

**Source:** session 2026-06-17 (moved from CLAUDE.md).

### Tests — co-located specs, shared mock providers

Unit tests are `**/*.spec.ts` co-located with source. Use `TestUtils.mockProviders([...])` from `test/test.utils.ts` — never roll your own mock providers. E2E tests are `test/*.e2e-spec.ts` with a 60s Jest timeout.

**Source:** session 2026-06-17 (moved from CLAUDE.md).
