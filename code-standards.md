# JS / TS Code Standards

Two-part doc:
1. **General standards** (Confluence baseline — short summary, link to source for the long version)
2. **Project-specific patterns** (harvested from sessions — what the user has corrected or reinforced)

Whenever ams-save runs, it adds findings from the conversation into part 2.

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

### Logger call — multi-line structured object, context last

```typescript
this.logger.error(
    {
        message: 'Short description',
        site,
        error: ex.message,
    },
    ex.stack,                   // only for .error()
    LoggingContexts.ACTIVE_VEHICLES,
);
```

First arg always a structured object, `message` first key. No inline single-line form. `.log()` / `.warn()`: second arg is the context. `.error()`: second arg is stack, third is context. Closing `);` on its own line.

**Source:** session 2026-05-20.

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
