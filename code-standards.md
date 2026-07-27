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
- **Avoid early returns** as an escape hatch. Push checks up to the caller. Exceptions: framework patterns (React `useEffect`), abstract util functions, and crawler skip/reject guards (`continue` in a listing loop on a missing required field, `return null` in `parseDealer` when there's no dealer, `if (!html) return` where the base doesn't already guarantee it) - these represent "stop processing this item entirely," not "compute one of several possible values," so they stay as guard clauses at the top of the function/loop rather than being folded into a single-return shape. See crawler-create skill for the crawler-specific version of this rule with examples (`resolveUrl`/`getNextPageUrl` in `PolovniAutomobili.service.ts`).
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

### Extract inline object types to named interfaces, even single-use or file-private ones

Applies in two situations: `Array<{ site: string; ratio: number }>` appearing on two or more signatures, AND a nested object shape sitting inline inside a single interface even if only used once. Give every nested shape its own `interface` - file-private/non-exported if it's not used outside the file.

```typescript
// BAD - repeated inline shape across signatures
private evaluateSiteLocks(...): { ...; newlyLocked: Array<{ site: string; ratio: number }> } | null {}
private notifyLockedSites(newlyLocked: Array<{ site: string; ratio: number }>, ...): Promise<void> {}

// BAD - inline nested shape inside a single interface, only used once
interface ProductData { images: Array<{ fileName: string }>; }
interface ContactDetails { address: { city: string; country: string }; }

// GOOD
export interface SiteLockEntry { site: string; ratio: number; }
private evaluateSiteLocks(...): { ...; newlyLocked: Array<SiteLockEntry> } | null {}
private notifyLockedSites(newlyLocked: Array<SiteLockEntry>, ...): Promise<void> {}

interface ProductImage { fileName: string; }
interface ProductData { images: Array<ProductImage>; }
interface ContactAddress { city: string; country: string; }
interface ContactDetails { address: ContactAddress; }
```

**Source:** session 2026-05-20, extended session 2026-07-10 (MAR-2126 polovni-automobili).

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

### Crawler service method order — two exceptions to "new methods go at the end"

For crawler `<Site>.service.ts` files specifically, the "new methods go at the end" rule (above) has two named exceptions, plus a required internal order for the public overrides and for the private-helper block:

1. **`fetchRequest` override goes first**, directly after the constructor — before any other public override, regardless of when it was added or where it sits in the base-class call order. It's infrastructure (proxy/browser strategy), not a lifecycle step, so it doesn't slot into call-order position.
2. **`beforeParseVehicle` goes immediately before `parseVehicleInput`** — it's the hook that runs right before `parseVehicleInput` and exists specifically to prep its context (e.g. setting a referer), so it reads better directly above it rather than wherever it was added.
3. **All other public lifecycle overrides** are ordered by the sequence the base class actually calls them in (see the crawler-create skill §3 execution-order diagram): `getBrandsAndModels` → `getVehicleListPageResponse` → `getNextPageUrl` → `beforeParseVehicle` → `parseVehicleInput` → `beforeParseDealer`/`parseDealer` → `afterParseVehicle` → any other override.
4. **Private helper methods go at the end of the file** (per the base rule above), but within that block they are ordered by first call site, not alphabetically/by topic/by add-date — the helper first reached in the flow (e.g. one called from inside `getVehicleListPageResponse`) comes before a helper only reached from `parseVehicleInput`, which comes before one only reached from `parseDealer`, etc.

```typescript
// 1. fetchRequest — always first override, right after the constructor
public async fetchRequest<R = string>(url: string, options: CrawlFetchRequestOptions = {...}): Promise<R | null> {
    return this.fetchRequestWrapper(url, options, (requestOptions) => {
        return this.browserService.startBrowserAndStaticVisitUrl<R>(url, this.site, requestOptions);
    });
}

// 2. remaining public overrides in base-class call order
async getBrandsAndModels(): Promise<Array<ParseVehicleParams>> { /* ... */ }
async getVehicleListPageResponse(options: VehicleListPageResponseOptions): Promise<VehicleListPageResponse> { /* ... */ }
getNextPageUrl(params: GetNextPageUrlParams): string | undefined { /* ... */ }

/**
 * Detail pages get flagged by cloudflare more than listing pages when visited cold - set the referer
 * to the listing page the vehicle was found on, so the visit looks like organic search-to-detail navigation
 */
async beforeParseVehicle(parseVehicleParams: ParseVehicleParams, fetchRequestOptions: CrawlFetchRequestOptions & { referer?: string }): Promise<boolean> {
    fetchRequestOptions.referer = parseVehicleParams.vehicleListUrl;
    return super.beforeParseVehicle(parseVehicleParams, fetchRequestOptions);
}

async parseVehicleInput(parseVehicleParams: ParseVehicleParams): Promise<AdVehicle | null> { /* ... */ }
async parseDealer(parseVehicleParams: ParseVehicleParams): Promise<RawDealerData | null> { /* ... */ }

// 3. private helpers at the end, ordered by first call site (earliest-reached first)
private buildListingPartial(...) { /* called from getVehicleListPageResponse */ }
private parsePrice(...) { /* called from parseVehicleInput */ }
private parseEquipment(...) { /* called from parseVehicleInput, after parsePrice in that method's body */ }
```

**Source:** session 2026-07-09 (Filip, polovni-automobili RS parser refactor).

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

**Caveat — single-file lint can still produce a noisy diff.** If the file predates the current Prettier/ESLint config (or was last touched before a config change), running `--write`/`--fix` on the *whole file* reformats every non-compliant line it finds, not just the ones you edited — e.g. `item => x` → `(item) => x`, ternary re-wrapping, `as X` → `(await ...) as X`. Always `git diff` after linting and check the hunks are limited to your actual change; if not, revert the file to HEAD and hand-apply your edit without running the whole-file formatter.

**Source:** session 2026-06-17 (moved from CLAUDE.md); caveat added session 2026-07-03 (AutohausListle.service.ts — whole-file prettier/eslint --fix reformatted ~10 unrelated lines, had to `git show HEAD:<file>` and reapply the minimal diff by hand).

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

### Log missing field names, not values — use Object.entries + filter

When guarding against missing required fields, compute which fields failed first using `Object.entries` + `filter`, then branch on `.length` with if/else (no early return). Use `errorCode` for the joined field names and `count` for how many failed.

```typescript
const missingFields = Object.entries({ brand, model, name, ident })
    .filter(([, value]) => typeof value !== 'string')
    .map(([field]) => field);

let result = null;

if (missingFields.length) {
    this.logger.warn({
        message: `${this.site} vehicle is missing info...`,
        site: this.site,
        errorCode: missingFields.join(', '),
        count: missingFields.length,
    }, LoggingContexts.PARSER_DEBUGGING);
} else {
    // happy path
    result = buildSomething();
}

return result;
```

**Source:** session 2026-06-17.

### Fix SVL field mismatches at the source selector, not by excluding the field

When SVL (`Listing vehicle check failed in prop`) fails on a field, don't drop it from the listing partial to make the comparison pass. Check whether the *same* underlying value is reachable on both listing and detail pages with a selector that agrees with what the detail-page parser resolves — the field almost always belongs in both places.

```typescript
// BAD — price kept mismatching, so it was removed from the listing partial entirely
return { rawBrand, rawModel, ...specPartial }; // no price/discountedPrice

// GOOD — root cause was the listing selector picking the wrong DOM element (a wishlist
// popup's stale price); once the listing used the same resolution logic as resolvePrice()
// on the detail page, both agreed and SVL passed
return { rawBrand, rawModel, price, discountedPrice, rawPrice, ...specPartial };
```

Removing a field from the listing partial should be a last resort, only when the site itself renders genuinely different information on listing vs. detail (e.g. listing never shows an MSRP that only exists on some detail pages) — not a reflex fix for "the values don't match yet".

**Source:** session 2026-07-01 (MAR-2113 rastetter — user rejected price/discountedPrice removal, root cause was a wrong `.first()` selector picking up a hidden wishlist-plugin price element instead of the visible current price).

### SVL field parity — listing and detail must resolve the same value the same way

For any field compared by SVL, the listing-page selector and the detail-page selector need *identical* disambiguation logic, not just "the field exists on both pages". A selector that happens to work on the detail page can silently pick up the wrong element on the listing page (or vice versa) if the two pages have different surrounding markup (e.g. related-product widgets, wishlist popups duplicating the same CSS class).

```typescript
// BAD — same selector, different contamination risk per page:
// on the detail page, .woocommerce-Price-amount also matches "Weitere Vorschläge" (related
// products) rendered further down the page, picking up a random other vehicle's price
const rawPriceText = loadedHtml('.woocommerce-Price-amount').first().text().trim();

// GOOD — scope out related-product loop items explicitly, and use a page-unique
// container (sticky checkout bar) that never repeats for related products
const rawPriceText = loadedHtml('.sticky-bottom-bar .woocommerce-Price-amount').first().text().trim();
const mainStrike = loadedHtml('.reg_price-text .strike')
    .filter((_, el) => loadedHtml(el).closest('.e-loop-item').length === 0)
    .first();
```

Verify with a live vehicle that has related products/recommendations rendered on its detail page — that's exactly where "same selector, different result" bugs hide.

**Source:** session 2026-07-01 (MAR-2113 rastetter — `.woocommerce-Price-amount.first()` on the detail page matched a related-product's price ~40% of the time).

### SVL field parity — strip seller-added marketing text from listing title before using it as `name`

Not every SVL `name` mismatch is a selector bug. Some sites let the seller free-type their listing title, and it can carry a trailing note the site itself strips out on the detail page (e.g. "(može zamena)" - "trade possible" - appended by the seller, present in the listing API's `title` field but absent from the detail API's `productData.title`). Both sides are individually correct per their own source field; the mismatch is a genuine site-level difference, not a wrong selector or a crawler bug.

Confirmed via a live check on both endpoints for the same ad: listing `title: "BMW M3 (može zamena)"` vs detail `productData.title: "BMW M3"` — the detail page normalizes it away, the listing page doesn't.

**Considered but reverted (2026-07-09):** stripping any trailing parenthetical (`.replace(/\s*\([^)]*\)\s*$/, '').trim()`) was tried, but flagged as unsafe before shipping - a generic strip can't distinguish a seller-added marketing badge from real trailing content that legitimately belongs in the title (e.g. "(170 KS)", "(Facelift)"), and since `VehicleHelper.isPartialVehicleSubsetOfVehicle` does strict `!==` equality with no fuzzy matching, a wrong strip on either side (or a title that never had marketing noise but has other trailing parens) creates a *new* SVL failure instead of fixing one. `CarGr.service.ts` strips a narrower pattern (`.replace(/\s*\([\d.,]+\)\s*$/, '').trim()`, numeric-only) which doesn't have this ambiguity - not a direct precedent for free-text stripping. Decision: leave `item.title` unstripped for now (`name` on the listing partial will occasionally mismatch detail and fail SVL for ads with a trailing marketing note) and revisit sizing the actual blast radius via a larger/stage-scale `crawler-data-validation` run before choosing between (a) narrowing the strip to the exact known phrase, or (b) dropping `name` from the listing partial's SVL-compared fields entirely.

**How this was caught:** the generic `crawler-data-validation` skill's Graylog G1 query (`message:"Details URL validation failed"`) does **not** match this site's actual log line — this site's SVL comparator (`VehicleHelper.isPartialVehicleSubsetOfVehicle` in `src/shared/helpers/vehicle.helper.ts`) logs `message:"Listing vehicle check failed in prop"` under `context:LISTING_VEHICLE_CHECK` instead. Both message shapes exist in the codebase for different SVL-adjacent checks - when validating a specific site, grep `src/shared/helpers/vehicle.helper.ts` for the exact log line used, don't assume the skill's default query string covers it. Confirmed the mismatch was live and reproducible in Graylog (Kibana dashboard showing 4 hits over a 15-minute window), then found the root cause via `grep -rn "LISTING_VEHICLE_CHECK" src/` and by live-diffing the listing vs. detail JSON for one of the flagged URLs. Verified the fix by rerunning the same brand+model and confirming the Graylog query dropped from 4 hits to 0.

**Source:** session 2026-07-09 (MAR-2126 polovni-automobili — user caught this in a live Graylog dashboard after the crawler-data-validation skill's default SVL query reported a false "0 failures").

### Derive SVL-compared fields from the card's own markup, not from an outer discovery-loop variable

When a crawler discovers listing URLs by looping over a filter dimension (brand → bodytype → model, category → subcategory, etc.) and a single entity can legitimately match more than one filter value, don't tag the entity with "whichever filter loop found it" — that value depends on iteration order/timing and will flip between crawls for any entity matching multiple filters. Derive the field from a taxonomy/class/attribute that's on the entity's own card HTML instead, with a fixed priority order for entities that carry multiple values.

```typescript
// BAD — rawBodyType comes from the OUTER fahrzeugtyp-filter loop; a van tagged with both
// 'vanupto7500' and 'boxtypedeliveryvan' on the site gets discovered via both filter loops,
// and whichever crawl finishes last wins — SVL then flip-flops between the two values forever
for (const bodyTypeEl of bodyTypeOptions) {
    const rawBodyType = getFirstElementTextTrimmed(bodyTypeEl);
    // ...pushes { additional: { rawBodyType } } per brand/model discovered under this filter
}

// GOOD — read the taxonomy classes directly off the card, same result regardless of
// which filter page rendered it, deterministic pick when several classes are present
const vehicleDesignPriority = ['limousine', 'estatecar', 'offroad', 'smallcar', 'cabrio', 'van', 'vanupto7500', 'boxtypedeliveryvan'];
private getVehicleDesignSlug(classes: string): string | null {
    const presentSlugs = classes.split(' ').filter((c) => c.startsWith('vehicle_design-')).map((c) => c.slice('vehicle_design-'.length));
    return vehicleDesignPriority.find((slug) => presentSlugs.includes(slug)) ?? null;
}
```

**Source:** session 2026-07-01 (MAR-2113 rastetter — user asked "we now loop by bodyType but we don't pass or use bodyType further??", surfacing that the outer loop's value was dead/unused after the fix and the loop itself was redundant since it discovered the exact same brand set as reading the base page once).

### Audit discovery loops for redundancy after changing how a downstream field is derived

After removing a field's threading from an outer loop (because it's now derived elsewhere), check whether the outer loop still does anything the base/simpler page doesn't already expose. Compare the two discovery sets directly before deciding to keep the extra loop.

```bash
# compare what looping through every filter page finds vs. reading the base page once
curl -s .../shop/fahrzeugtyp-van/ | grep -o 'brands-[a-z-]*' | sort -u   # per-filter loop
curl -s .../shop/ | grep -o 'brands-[a-z-]*' | sort -u                  # base page
# identical sets → the outer loop is pure overhead (redundant re-crawls of the same brand/model)
```

**Source:** session 2026-07-01 (MAR-2113 rastetter — the bodytype-filter outer loop in `getBrandsAndModels()` found the exact same 17 brands as reading `/shop/` once, while also causing duplicate brand+model discovery for any multi-tagged vehicle).

### Avoid dynamic Elementor/plugin-generated selectors — prefer semantic, single-purpose markup

`data-id`/`elementor-element-<hash>` attributes and hidden plugin widgets (wishlist popups, tooltips) regenerate or duplicate content when the page template is re-saved, and can silently match the wrong element. Prefer classes tied to the widget's *purpose* (a sticky checkout bar, a named form field) that only appear once per page and aren't reused by unrelated plugins.

```typescript
// BAD — Elementor-generated widget ID, changes on template re-save
loadedHtml('[data-id="abb3c2e"] h2.elementor-heading-title').first();

// BAD — wishlist plugin duplicates the price in a hidden div; works today, not guaranteed tomorrow
loadedHtml('.wlfmc-parent-product-price .woocommerce-Price-amount').first();

// GOOD — purpose-named, single-occurrence per page
loadedHtml('.sticky-bottom-bar .woocommerce-Price-amount').first();
```

**Source:** session 2026-07-01 (MAR-2113 rastetter — user: "you took dynamic selector [data-id=\"abb3c2e\"] that can change per request or per day, this is a total no go" / "i dontt believe wishlist is reliable longterm").

### Check `CrawlerHelper` for an existing URL/string utility before writing manual parsing

`CrawlerHelper` already has `setQueryStringParameter`, `getQueryStringParameter`, `deleteQueryStringParameter(s)`, `deleteAllParametersFromUrl`, `deleteHashParameterFromUrl`, `getBaseUrl`, `incrementPageQueryStringParameter`. Check these before reaching for `.split('?')`/regex on a URL string — even if the exact helper doesn't fit (e.g. `incrementPageQueryStringParameter` is query-string-only and won't help with path-segment pagination), a partial one usually does.

```typescript
// BAD
const currentBase = url.split('?')[0];

// GOOD
const currentBase = CrawlerHelper.deleteAllParametersFromUrl(url);
```

**Source:** session 2026-07-01 (MAR-2113 rastetter — user: "cant we youst use incrementPageQueryStringParameter or some other helper?" then "and you can undo and do with crawler helpers?").

### Collapse sequential guard clauses into one boolean-expression return

When a function has 2+ sequential `if (!x) return undefined;` guards before a single final return, prefer one expression that ANDs the conditions together, rather than early-returning from each check individually.

```typescript
// BAD — three separate exit points to trace
public getNextPageUrl(params): string | undefined {
    if (!maxPage || nextPage > maxPage) {
        return undefined;
    }
    if (!currentBase) {
        return undefined;
    }
    return `${currentBase}/page/${nextPage}/`;
}

// GOOD — one return, the whole precondition is visible in one line
public getNextPageUrl(params): string | undefined {
    return maxPage && nextPage <= maxPage && currentBase ? `${currentBase}/page/${nextPage}/` : undefined;
}
```

**Source:** session 2026-07-01 (MAR-2113 rastetter — user: "nto fan of regexes and early returns, can you do it somwhow different?").

### No blank line between simple consecutive `readonly` property declarations

Class-level `readonly` fields that are simple one-liners (no docblock, no object literal) go directly under each other, no blank line. Reserve blank lines for grouping around fields that carry their own docblock or a multi-line initializer.

```typescript
// BAD
readonly country: CountryInfo = CountryInfoMap.DE;

readonly shopUrl: string = `${this.baseUrl}/shop`;

// GOOD
readonly country: CountryInfo = CountryInfoMap.DE;
readonly shopUrl: string = `${this.baseUrl}/shop`;
```

**Source:** session 2026-07-01 (MAR-2113 rastetter — user correction).

### Exclude unrelated lockfile/dependency bumps from ticket-scoped commits

If `package-lock.json` shows a dependency version bump unrelated to the current ticket (picked up incidentally from an `npm install` run during the session), revert that file before committing — it doesn't belong in a crawler-fix PR and should land as its own dedicated change if intentional.

```bash
git checkout develop -- package-lock.json   # before committing, if the diff is unrelated
```

**Source:** session 2026-07-01 (MAR-2113 rastetter — user: "you should commit packege lock json and update it, revert that").

### Use JSDoc docblocks above methods, not inline comments

Private and public methods get a `/** ... */` docblock, not a `//` comment above them. Inline `//` comments inside method bodies are only for non-obvious WHY, not for describing the method itself.

```typescript
// BAD
// tries MM/YYYY first, falls back to year-only
private parseDateOfFirstRegistration(raw: string): string | null { ... }

// GOOD
/**
 * Listings expose year only; details expose MM/YYYY or bare YYYY.
 * Tries MM/YYYY first, falls back to year-only so SVL comparison stays consistent.
 */
private parseDateOfFirstRegistration(raw: string): string | null { ... }
```

**Source:** session 2026-06-17.

### Verify automated review comments (Gemini/CodeRabbit/etc.) against current code before applying

Line numbers and surrounding context in an automated review comment reflect the file state *when the review ran*, not necessarily HEAD. If the file was rewritten in later commits (common in a multi-round session), the comment can be stale — already fixed differently, referencing code/features that no longer exist, or suggesting a regression back to an earlier, worse approach. Check the current file at that location before applying; don't apply on the strength of the suggestion's confidence or priority badge alone.

```typescript
// A Gemini "high priority" comment suggested adding a KW→HP fallback + explicit `data:` URI
// checks to a regex-based mileage/horsepower parser. Checking the CURRENT file showed:
// - the base64/data-src ordering was already fixed (data-src checked first)
// - the flagged regex no longer existed — replaced by simpler string checks earlier in the session
// - applying the suggested KW-fallback would have been guarding a case confirmed absent
//   in 106/106 live listings sampled across all 16 brand pages
// Only 1 of 4 comments on that PR was still applicable to HEAD.
```

**Source:** session 2026-07-01 (MAR-2113 rastetter — reviewed Gemini PR #77 comments against current `Rastetter.service.ts`, 3 of 4 were stale from an earlier revision).

### Don't guard cheerio `.attr()` / `DataHelper.normalizeNumericValue()` with `.length > 0` checks

Both already resolve safely on empty/missing input — a `.length > 0 ? x.attr(...) : undefined` or a separate "extra safety" cross-check element is dead weight, not defensive code. `cheerio.attr()` on an empty selection returns `undefined` (no throw); `DataHelper.normalizeNumericValue(undefined)` returns `null`. Chain directly.

```typescript
// BAD - redundant guards
const nextPageLink = loadedHtml('a.next').length > 0 ? loadedHtml('a.next') : undefined;
const nextPageNumber = nextPageLink ? DataHelper.normalizeNumericValue(nextPageLink.attr('data-page')) : undefined;

// GOOD - both calls are already null-safe
const nextPageNumber = DataHelper.normalizeNumericValue(loadedHtml('a.next').attr('data-page'));
```

**Source:** session 2026-07-03 (MAR-2039 autohaus-listle — user removed both the `.length > 0` guard on the next-page link and a separate "extra safety" last-page cross-check after the selector's own `:not(.disabled)` condition already made them redundant).

### Cheerio `.find()` only searches descendants — check the element itself first

`el.find(selector)` never matches `el` itself, only its children. If the class/attribute you're after is commonly on the card/row element itself (not a nested wrapper), `.find()` silently returns an empty selection and every downstream extraction from it goes null with no error. Verify with `el.hasClass(...)` / inspect the raw HTML before assuming a class lives on a descendant.

```typescript
// BAD — 'product' is a class on the .e-loop-item element itself, not a descendant;
// vehicleEl.find('.product') always returns empty, classes becomes '', every
// taxonomy-class extraction (bodyType, fuelType, transmission) silently returns null
const vehicle = vehicleEl.find('.product').first();
const classes = vehicle.attr('class') || '';

// GOOD — the classes are already on vehicleEl itself
const classes = vehicleEl.attr('class') || '';
```

If you genuinely need resilience against the site later moving those classes onto a nested child, use a self-or-descendant union instead of plain `.find()`:

```typescript
const vehicle = vehicleEl.filter('.product').add(vehicleEl.find('.product')).first();
const classes = vehicle.attr('class') || '';
```

**Why this stayed hidden for other fields:** if the detail page also carries a labeled fallback for the same field (e.g. `detailsDict['Kraftstoff'] || partialVehicle?.rawFuelType`), the listing-side `.find()` bug is masked — only fields with no such detail-page label (like `rawBodyType`, sourced only from the listing partial) fully expose it. When one field is null but a sibling field extracted with the exact same `classes` string works, suspect a fallback masking the same bug elsewhere, not that only one selector is broken.

**Source:** session 2026-07-06 (MAR-2113 rastetter — `bodyType` was `null` on 100% of prod vehicles, including fresh full-detail-visit crawls, while `fuelType`/`transmission` extracted from the same broken `classes` string worked fine via a detail-page fallback that `bodyType` didn't have).

### `.attr(name)` looks up a literal attribute, it is not a selector check

`.attr('.foo')` looks for an HTML attribute literally named `.foo` (which doesn't exist) — it always returns `undefined`. To check whether an element matches a class/selector, use `.hasClass()`, `.is(selector)`, or `.filter(selector)` (the latter two accept full CSS selectors, `.hasClass()` only a bare class name).

```typescript
// BAD — .attr() never does selector matching
const classes = vehicle.attr('.product') || '';

// GOOD
const isProduct = vehicleEl.hasClass('product'); // bare class name
const isProduct2 = vehicleEl.is('.product');     // any selector
```

**Source:** session 2026-07-06 (MAR-2113 rastetter — user asked "can we maybe just do const classes = vehicle.attr('.product')?" while iterating on the `.find('.product')` fix above).

### Rule out systemic/shared-pipeline bugs by comparing against 2-3 other sites on the same code path first

When a field is null/wrong for one site and the suspect code lives in a shared abstract class or pipeline stage, don't assume the shared code is broken — run the identical check against 2-3 other sites that go through the exact same shared step. If they're fine, the bug is almost certainly in the one site's own crawler, not the shared layer; this rules out an entire investigation branch in a couple of ES queries instead of hours reading shared-pipeline code.

```bash
# same aggregation, 3 different sites, same shared mapRawValues() step
for site in mobile otomoto brueggemann; do
  curl -s "$ES/marketstudy_search_rollover/_search" -d "{\"query\":{\"bool\":{\"must\":[{\"term\":{\"Site\":\"$site\"}},{\"term\":{\"IsListingValidatedVehicle\":false}}]}},\"aggs\":{\"has_bodytype\":{\"filter\":{\"exists\":{\"field\":\"BodyType\"}}}}}"
done
# all ~100% coverage → shared step is fine, bug is in the ONE site not matching this pattern
```

**Source:** session 2026-07-06 (MAR-2113 rastetter — `bodyType` null looked like it could be a `mapRawValues`/SVL-pipeline-wide gap; checking mobile.de, otomoto, and Brueggemann (same shared code, same SVL pattern) at ~100% coverage immediately proved it was Rastetter-only, redirecting the investigation back to `Rastetter.service.ts` instead of the shared abstract classes).

### Before reusing a named feature branch, confirm its PR wasn't already merged

If asked to commit to a previously-used branch name, check whether that branch's PR already merged and the remote branch was deleted (`git fetch origin <branch>` failing, or `gh pr view <PR#> --json state,mergedAt`) before pushing more commits onto the stale local copy. If merged, rebuild the branch fresh from `origin/develop`, reapply just the new change, and push as a new branch/PR — don't resurrect the old, now-diverged branch.

```bash
git fetch origin <branch-name>   # "couldn't find remote ref" → branch was deleted (merged)
git branch -D <branch-name>
git checkout -b <branch-name> origin/develop
git apply /tmp/my-change.patch   # or cherry-pick / re-apply the intended diff
```

**Source:** session 2026-07-06 (MAR-2113 rastetter — PR #77 had already merged and its branch was auto-deleted by GitHub days earlier; the stale local branch still existed and would have produced a confusing diff against current develop if reused as-is).

### Widen visibility directly, don't add a pass-through wrapper method

If an external caller needs a `protected` method, don't add a `public` wrapper method that just calls it — TypeScript allows widening visibility (`protected` → `public`) directly in a subclass override, so change the modifier on the existing override instead. A wrapper adds an indirection layer with zero actual access control benefit.

```typescript
// BAD — wrapper adds nothing, mapRawValues stays effectively public anyway
public async applyRawValuesMapping(vehicle: AdVehicle): Promise<void> {
    await this.mapRawValues(vehicle);
}
protected async mapRawValues(vehicle: AdVehicle | Partial<AdVehicle>, addDefaultsAndCalculations = true): Promise<void> { ... }

// GOOD — widen the existing override directly
public async mapRawValues(vehicle: AdVehicle | Partial<AdVehicle>, addDefaultsAndCalculations = true): Promise<void> { ... }
```

**Source:** session 2026-07-08 (MAR-2039 — `crawler.controller.ts` needed to call `VehicleAdCrawlerAbstract.mapRawValues` from the `/crawl-vehicle` debug endpoint).

### Prefer `.toString()` over `String(x)`

`.toString()` is the house convention (236 vs 19 occurrences repo-wide). Use `x?.toString()` when `x` might be `null`/`undefined` - `String(x)` silently converts those to the literal strings `"null"`/`"undefined"` instead of propagating "no value", which is worse than the `TypeError` a bare `.toString()` would throw.

```typescript
// BAD
const rawYear = String(productData.year);

// GOOD
const rawYear = productData.year?.toString();
```

**Source:** session 2026-07-10 (MAR-2126 polovni-automobili).

### Check `typeof` before negating an optional boolean flag

`!undefined` and `!null` both evaluate to `true` - blindly negating an optional source flag silently asserts the opposite of "unknown" instead of propagating "unknown".

```typescript
// BAD - conditionNew missing/null silently becomes isUsed: true
const isUsed = !item.conditionNew;

// GOOD
const isUsed = typeof item.conditionNew === 'boolean' ? !item.conditionNew : undefined;
```

**Source:** session 2026-07-10 (MAR-2126 polovni-automobili).

### Don't interpolate an optional field into a URL template literal without guarding it

An unset field silently produces a URL ending in the literal string `undefined` instead of no URL at all.

```typescript
// BAD - urlAlias missing → siteUrl = "https://example.com/undefined"
const siteUrl = `${this.baseUrl}/${contactDetails.urlAlias}`;

// GOOD
const siteUrl = contactDetails.urlAlias ? `${this.baseUrl}/${contactDetails.urlAlias}` : undefined;
```

**Source:** session 2026-07-10 (MAR-2126 polovni-automobili).

### Build a multi-part optional address with `${a || ''} ${b || ''}`.trim(), not a ternary

Established pattern across several crawlers (`AutoScout`, `Biltorvet`, `GarageGros`, `OlxRo`, `Rastetter`) for joining optional string parts into one display field - each part defaults to `''` so a missing piece doesn't produce `undefined`/`null` in the output, and `.trim()` cleans up the resulting extra whitespace when a part is missing.

```typescript
// BAD - ternary that only handles the both-present/both-missing cases explicitly
const fullAddress = address && city ? `${city}, ${address}` : country;

// GOOD
const fullAddress = `${city || ''} ${address || ''}`.trim() || country;
```

**Source:** session 2026-07-10 (MAR-2126 polovni-automobili).

### Filter cheerio sibling text nodes with `el.type === 'text'`, not a DOM `Node` cast or regex

When two pieces of data live as adjacent text nodes inside the same element (e.g. street address and zip code separated by a `<br>`, with no wrapping tags), use cheerio's own `.contents()` + `el.type === 'text'` filter to pull them apart - it's already an established pattern (`Mobile.service.ts`) and needs no extra import or type cast. Reached for both a regex on the concatenated text and a `(el as unknown as Node).nodeType === 3` cast first - both were rejected as more complicated than necessary.

```typescript
// GOOD
const [address, zip] = addressElement
    .contents()
    .filter((_, el) => el.type === 'text')
    .map((_, el) => $(el).text().trim())
    .get();
```

**Source:** session 2026-07-13 (MAR-2129 auto1).

### Set `_id` explicitly on any ES bulk `index` action keyed by a domain id

When bulk-indexing documents that have their own natural id (e.g. `storeId`), always pass `_id` on the `index` action. Omitting it lets ES auto-generate a random id, which silently breaks every other piece of code that looks the document up or deletes it by that domain id (404s that look like an unrelated bug).

```typescript
// BAD
operations.push({ index: { _index: index } });
operations.push(cleanDoc);

// GOOD
operations.push({ index: { _index: index, _id: doc.storeId } });
operations.push(cleanDoc);
```

**Source:** session 2026-07-21 (MAR-1975 export/import — found via `deleteDataVehicleByStoreId` failing with 404 not_found on freshly-imported data).

### Never pre-resolve a `ConfigKeys` value before passing it to a method that resolves it itself

If a service method's signature takes a `bucket: ConfigKeys` (or similar) and internally does `this.configService.get(bucket)`, callers must pass the raw enum key, not an already-resolved string. Resolving it at the call site too causes a double-resolution: the method looks up the resolved *value* as if it were a *key*, gets `undefined`, and fails downstream in a way that doesn't point back to this line.

```typescript
// BAD - double resolution, bucket ends up undefined inside getVehicleByUrl
const bucket = this.configService.get(ConfigKeys.AWS_S3_BUCKET_STORE_VEHICLE);
await this.storeVehicleService.getVehicleByUrl(url, bucket);

// GOOD - pass the raw key, let the callee resolve it once
await this.storeVehicleService.getVehicleByUrl(url, ConfigKeys.AWS_S3_BUCKET_STORE_VEHICLE);
```

**Source:** session 2026-07-21 (MAR-1975 export/import — 100% of S3 reads/writes failing with "No value provided for input HTTP label: Bucket").

### `fetchRequest` options object replaces the default entirely — only pass fields you're overriding

`fetchRequest`'s default param object (`{ method: 'GET', followRedirect: false, rejectUnauthorized: true, useRedisCache: false, useS3Cache: true, useProxy: false }`) only applies when the `options` argument is omitted entirely — passing any object replaces it wholesale, it does not merge. Spelling out every field is redundant: `fetchRequestWrapper` re-applies `useS3Cache`/`useRedisCache` defaults via `??` regardless, and downstream (`request.service.ts`, `RequestHelper.getMaxRedirects`) every other field is read with `??`/falsy-checks/`=== false` comparisons that treat `undefined` identically to the "default" value. Only pass the field(s) actually being overridden.

```typescript
// BAD - spells out every default, all of which behave identically to omitting them
const html = await this.fetchRequest(this.baseUrl, {
    method: 'GET', followRedirect: false, rejectUnauthorized: true,
    useRedisCache: false, useS3Cache: false, useProxy: false,
});

// GOOD
const html = await this.fetchRequest(this.baseUrl, { useS3Cache: false });
```

**Source:** session 2026-07-31 (MAR-2039 AutoScout).

### Cross-check a "top"/quick-pick subset against the full list before merging both into a taxonomy source

Sites often expose a small "featured"/"top" bucket alongside a full "other"/"all" list for the same taxonomy (brands, categories). Before concatenating both as if they're disjoint, diff their entries — the "top" bucket is frequently a duplicated subset of the full list (same ids), existing only for a UI quick-pick section. Concatenating both without checking doubles the affected entries (duplicate model-API fetches, duplicate listingUrls).

```typescript
// verify before merging: is topMakes a subset of otherMakes (same ids)?
const top = new Set(topMakes.map(m => m.id));
const other = new Set(otherMakes.map(m => m.id));
console.log('overlap:', [...top].filter(id => other.has(id)).length, '/', top.size);
```

**Source:** session 2026-07-31 (MAR-2039 AutoScout — `topMakes` was a full duplicate of 7 entries already present in `otherMakes`; only `otherMakes` was needed).

### Prefer a targeted regex over brace-counting to extract a JSON sub-value, when the target is verified flat

When a value must be sliced out of an otherwise-invalid JSON blob (e.g. a `window.__X__ = {...}` script containing stray `undefined` literals elsewhere), don't default to hand-rolled brace-depth counting. If the target array/object's own entries are flat (no nested `[`/`]`/`{`/`}`), a single non-greedy regex is simpler and equally correct — verify the "flat" assumption against real sample data first, since a nested target would break a naive regex silently.

```typescript
// verified flat entries ({id, name} only, no nested brackets) -> regex is safe and simpler
const otherMakesJson = scriptText?.match(/"otherMakes":\{[^}]*?"makes":(\[.*?\])\}/)?.[1];
// vs. hand-rolled brace-depth loop, only needed for genuinely nested/arbitrary-depth targets
```

**Source:** session 2026-07-31 (MAR-2039 AutoScout — user: "cant we do it with, i dont know, just regex or something?"; verified against real data that brand entries have no nested brackets before switching).

### Comment on non-obvious mechanics describes what it does, not the historical why

A docblock/comment above a regex, algorithm, or extraction step should state what it matches/does in one line — not narrate the site-restructure history that led to writing it that way (that belongs in the commit message / PR description, not the code).

```typescript
// BAD - historical narrative
// Brand dropdown on the homepage no longer renders a <select id="make"> with <option> elements.
// Brand id/name pairs now live only in the window.__INITIAL_STATE__ JSON blob embedded in a <script> tag.

// GOOD - states what the code does
// Captures the "makes" array inside "otherMakes":{"label":"...","makes":[...]} as group 1
```

**Source:** session 2026-07-31 (MAR-2039 AutoScout — user: "i dont need historical report, suggest me simple docblock what this method does").
