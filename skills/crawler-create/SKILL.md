---
name: crawler-create
description: Use when adding a new crawler site or source to the Market Study project — covers site analysis, WAF/proxy decisions, file checklist, listings-only vs detail mode, pagination patterns, and module registration. Trigger on "add crawler", "new source", "implement [site]", or when crawler-debug confirms a site needs a fresh implementation.
---

# crawler-create

## Overview

Step-by-step guide for implementing a new AMS (Market Study) crawler from scratch. Covers everything from site reconnaissance through module registration and local end-to-end test.

## Pre-Implementation Site Analysis

Before writing a single line of code, answer these questions by fetching the site:

| Question | Impact |
|---|---|
| Does direct curl return 200 or 403/blocked? | Determines proxy strategy |
| Is the page SSR (HTML contains data) or CSR (skeleton + XHR)? | SSR = no render needed; CSR = may need browser |
| Does the site have detail pages with extra data? | Listings-only vs full detail crawler |
| What is the pagination mechanism? (`page=N`, `pagina=N`, `offset=N`, infinite scroll)? | Drives `getNextPageUrl` implementation |
| Is data in JSON-LD (`<script type="application/ld+json">`), embedded JS state, or raw HTML? | Drives parsing strategy |
| How is the brand/model loop structured? (all-brands search, or per-brand/model URLs?) | Drives `getBrandsAndModels` |

### WAF / Proxy Decision

```
Direct curl → 403?  →  Try ScrapeDo proxy-only (1 credit, no render, no geoCode)
                            Still 403?  →  Add geoCode matching site country
                                Still 403?  →  Add render=true (5 credits, datacenter)
                                    Still blocked?  →  super=true (10 credits, residential)
SSR page?  →  Use ScrapeDo proxy-only (cheapest)
CSR page?  →  Needs render=true minimum
```

Use `ScrapeDoProxyConfig` with `superAtRetry`/`browserAtRetry` set to escalate on retries only — don't pay premium on first attempt.

### Listings-Only vs Detail Crawler

Gaspedaal-style aggregators (no owned detail pages) → listings-only:
- In `getVehicleListPageResponse` set `skipVisitingDetail: true` on the returned `VehicleListItem`
- `parseVehicleInput` must work from listing data only (no second fetch)
- `parseDealer` can return `null`/`undefined`

## File Checklist (5 files + 2 registrations)

```
src/crawler/sites/<SiteName>/
  <SiteName>.service.ts          ← main crawler service
  interfaces/
    <SiteName>ListingItem.interface.ts   ← TypeScript shape for one listing
    (optional) <SiteName>ApiResponse.interface.ts

src/shared/const/SiteKeys.ts     ← add to AvailableAdSiteKeysEnum
src/shared/const/CrawlingSites.ts  ← add URL + options
src/crawler/crawler-aliases.module.ts  ← import + add to SERVICE_PROVIDERS
```

## Service File Structure

```typescript
@CrawlerAlias(SiteKeysEnum.MY_SITE)          // links decorator → SiteKey
@Injectable()
export class MySiteService extends HtmlAdVehicleCrawlerAbstract {
    readonly country: CountryInfo = CountryInfoMap.NL;   // required abstract

    // ScrapeDo: inject only when WAF blocks direct requests
    private readonly proxyConfig: ScrapeDoProxyConfig = {
        superAtRetry: null,          // null = never escalate to residential
        browserAtRetry: null,        // null = never escalate to render
        superBrowserAtRetry: null,
    };

    constructor(
        public configService: ConfigService<EnvValidationSchema>,
        public rmqService: RmqService,
        public logger: LoggerService,
        public crawlerService: CrawlerService,
        public redisService: RedisService,
        public s3Service: S3Service,
        public requestService: RequestService,
        public dataMapperService: DataMapperService,
        private scrapeDoService: ScrapeDoService,   // add only when using ScrapeDo
    ) {
        super(configService, rmqService, logger, crawlerService, redisService, dataMapperService, s3Service, requestService);
    }

    // Override fetchRequest to route through ScrapeDo (omit if direct requests work)
    public async fetchRequest<R = string>(url: string, options = { ... }): Promise<R | null> {
        return this.fetchRequestWrapper(url, options, (requestOptions) =>
            this.scrapeDoService.request({ url, site: this.site, retryNr: requestOptions.retryNr, proxyConfig: this.proxyConfig })
        );
    }

    // Returns one ParseVehicleParams per brand/model combo (or one global entry for aggregators)
    async getBrandsAndModels(): Promise<ParseVehicleParams[]> { ... }

    // Parses one listing page into VehicleListItem[]
    async getVehicleListPageResponse(options: VehicleListPageResponseOptions): Promise<VehicleListPageResponse> { ... }

    // Returns next page URL or undefined when exhausted
    getNextPageUrl(params: GetNextPageUrlParams): string | undefined { ... }

    // Maps raw listing/detail data → AdVehicle
    parseVehicleInput(params: ParseVehicleParams): AdVehicle { ... }

    // Returns dealer data or null/undefined (null = private seller / not available)
    parseDealer(params: ParseDealerParams): RawDealerData | undefined { ... }
}
```

## Common Patterns

### JSON-LD ItemList (SSR aggregators like gaspedaal)

```typescript
// In getVehicleListPageResponse:
const parsed = JSON.parse($(html).find('script[type="application/ld+json"]').first().text());
const items: ItemListElement[] = parsed.itemListElement;
```

### `pagina=N` / `page=N` pagination

```typescript
getNextPageUrl({ options }: GetNextPageUrlParams): string | undefined {
    const currPage = options.currentPage;
    // stop condition: no more items OR hit paginationLimit
    if (options.html /* has items */ && currPage < this.paginationLimit) {
        return CrawlerHelper.setQueryStringParameter(options.options.nextPageUrl, 'pagina', String(currPage + 1));
    }
}
```

### Listings-only (skip detail fetch)

```typescript
vehicleListItems.push({
    vehicle: partialVehicle,
    vehicleListUrl: listingPageUrl,
    url: vehicleDetailUrl,         // still required for dedup key
    skipVisitingDetail: true,      // ← prevents second fetch
});
```

## SiteKeys Registration

```typescript
// src/shared/const/SiteKeys.ts — AvailableAdSiteKeysEnum
MY_SITE = 'my-site',              // kebab-case, matches siteKey value

// src/shared/const/CrawlingSites.ts — AdCrawlingSites
[AdSiteKeysEnum.MY_SITE]: {
    url: 'https://www.mysite.nl',
    shouldValidateListingVehicle: true,
    // routingKey: RmqBindings.MS_..._LISTING_URLS_TO_FETCH  ← add for high-volume sites
},
```

## Module Registration

```typescript
// src/crawler/crawler-aliases.module.ts
import { MySiteService } from '@crawler/sites/MySite/MySite.service';
// ... inside SERVICE_PROVIDERS array:
MySiteService,
```

## AdVehicle Field Mapping Quick Reference

| AdVehicle field | Typical source |
|---|---|
| `rawBrand` / `rawModel` | From `getBrandsAndModels` loop or listing field |
| `price` | numeric EUR value |
| `rawPrice` | `price.toString()` |
| `mileage` | km integer |
| `rawMileage` | original string |
| `rawFuelType` | site string (mapped by DataMapperService) |
| `rawTransmission` | site string |
| `rawBodyType` | site string |
| `rawColour` | site string |
| `coverImageUrl` | first image URL |
| `url` | canonical detail/listing URL (used as dedup key) |
| `vehicleListUrl` | the SRP page URL this vehicle was found on |
| `isOnStock` | `true` unless site indicates otherwise |
| `isToOrder` | `false` unless site has new-order listings |
| `isDamaged` | `false` unless site has salvage flag |

## Verification

After implementing, run:
```bash
# end-to-end local test
crawler-test-flow my-site

# (if paginating) check ES has vehicles from multiple pages:
crawler-data-validation my-site
```
