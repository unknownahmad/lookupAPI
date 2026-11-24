# LOOKUPAPI — Verified Free Public API Catalogue Report

**Date Tested:** 2026-11-22  
**Strict Requirement:** Zero authentication (no API keys, tokens, accounts, or registration), meaningful GET response data, and documented free public access terms.

## 1. Research Summary

- **APIs.guru directory entries discovered:** 2529
- **Phase 1 (APIs.guru automated scanner):** 115 APIs tested -> 17 `WORKING_NO_AUTH`, 44 `AUTH_REQUIRED`, 13 `UNAVAILABLE`, 41 `INCONCLUSIVE`.
- **Strict audit of Phase 1 `WORKING_NO_AUTH` results:** 14 of 17 were rejected (health checks, timestamps, status pages, staging hosts, or commercial APIs whose real endpoints require keys); **3 passed** (`APIs.guru`, `Forem API V1 (DEV.to)`, `CIRCL Hashlookup API`).
- **Phase 2 (Additional curated public API research):** 17 additional well-documented open/government/community APIs tested live via unauthenticated `GET` -> 1 rejected (`REST Countries API v3.1` returned a live HTTP 200 deprecation error requiring migration to key-gated v5), **16 passed**.
- **Total unique APIs tested across both phases:** 132 (115 in Phase 1 + 17 new candidates in Phase 2, plus re-verification of the 3 Phase 1 winners on rich data endpoints).
- **Final approved catalogue:** **15 APIs** across all **8 target categories** (15 distinct providers), stored in `data/verified_free_apis.json`. Four additional passing candidates (`Open-Meteo Geocoding API`, `Spaceflight News API v4`, `Hacker News API`, `Wikipedia REST API`) were verified HTTP 200 and documented below as optional backups to keep the primary catalogue within the 10–15 API target.

## 2. Approved APIs (15 Verified Candidates)

| # | Category | API Name | Provider | Endpoint | HTTP | Time | Auth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Weather | Open-Meteo Weather Forecast API | Open-Meteo | `GET /forecast?latitude=52.52&longitude=13.41&current_weather=true` | 200 | 0.172s | NONE |
| 2 | Weather | National Weather Service (NWS) API | NOAA / National Weather Service | `GET /points/38.8894,-77.0352` | 200 | 0.225s | NONE |
| 3 | Finance | Frankfurter Exchange Rates API | Frankfurter (ECB Data) | `GET /latest?base=EUR&symbols=USD%2CGBP%2CJPY` | 200 | 0.181s | NONE |
| 4 | Finance | U.S. Treasury Fiscal Data API | U.S. Department of the Treasury | `GET /v2/accounting/od/debt_to_penny?page%5Bsize%5D=2&sort=-record_date` | 200 | 0.61s | NONE |
| 5 | Geography | Zippopotam.us Postal Code API | Zippopotam.us (GeoNames Data) | `GET /us/90210` | 200 | 0.233s | NONE |
| 6 | Science | USGS Earthquake Hazards Program API | U.S. Geological Survey | `GET /query?format=geojson&limit=2&minmagnitude=4.0` | 200 | 0.508s | NONE |
| 7 | Science | PubChem PUG REST API | NIH / National Library of Medicine | `GET /compound/name/aspirin/property/MolecularFormula,MolecularWeight,IUPACName/JSON` | 200 | 0.281s | NONE |
| 8 | Education | Open Library Search API | Internet Archive | `GET /search.json?q=python+programming&limit=2&fields=title%2Cauthor_name%2Cfirst_publish_year%2Cedition_count` | 200 | 2.143s | NONE |
| 9 | Education | Crossref REST API | Crossref | `GET /works?query=machine+learning&rows=2&select=DOI%2Ctitle%2Cpublisher%2Ctype` | 200 | 0.381s | NONE |
| 10 | Technology | Forem API V1 (DEV.to) | Forem / DEV Community | `GET /articles?tag=python&per_page=2` | 200 | 0.295s | NONE |
| 11 | Technology | CIRCL Hashlookup API | CIRCL Luxembourg | `GET /lookup/md5/8ED4B4ED952526D89899E723F3488DE4` | 200 | 0.163s | NONE |
| 12 | Entertainment | PokéAPI (v2) | PokéAPI | `GET /pokemon?limit=3&offset=0` | 200 | 0.225s | NONE |
| 13 | Entertainment | TVmaze API | TVmaze | `GET /search/shows?q=sherlock` | 200 | 0.188s | NONE |
| 14 | Open Data | APIs.guru OpenAPI Directory API | APIs.guru | `GET /metrics.json` | 200 | 0.196s | NONE |
| 15 | Open Data | World Bank Indicators API (v2) | The World Bank | `GET /country/WLD/indicator/SP.POP.TOTL?format=json&per_page=2` | 200 | 0.29s | NONE |

### Why Each API Was Accepted

#### Open-Meteo Weather Forecast API (Weather)
- **Provider:** Open-Meteo
- **Base URL:** `https://api.open-meteo.com/v1`
- **Verified GET Endpoint:** `GET /forecast` (Query params: `latitude=52.52&longitude=13.41&current_weather=true`)
- **Live Test Result:** HTTP `200` in `0.172s` on `2026-11-22`
- **Documentation:** https://open-meteo.com/en/docs
- **Free Access Evidence:** Official docs state no API key or registration is required for non-commercial use (up to 10,000 calls/day); weather data licensed under CC BY 4.0 and source code under AGPLv3.
- **Acceptance Rationale:** Returned live Berlin meteorological metrics (temperature, wind speed, wind direction, weather code) in 0.172s with zero authentication. Official docs explicitly confirm free keyless non-commercial use up to 10,000 calls/day under CC BY 4.0 data licensing.

#### National Weather Service (NWS) API (Weather)
- **Provider:** NOAA / National Weather Service
- **Base URL:** `https://api.weather.gov`
- **Verified GET Endpoint:** `GET /points/38.8894,-77.0352` (Query params: `None`)
- **Live Test Result:** HTTP `200` in `0.225s` on `2026-11-22`
- **Documentation:** https://www.weather.gov/documentation/services-web-api
- **Free Access Evidence:** U.S. Government public domain service; official docs state no API key or account is required, only a descriptive User-Agent header.
- **Acceptance Rationale:** Official U.S. Government (NOAA) public domain service returning structured GeoJSON forecast grid links, weather office details, and station coordinates in 0.225s with no API key (requires only a descriptive User-Agent header).

#### Frankfurter Exchange Rates API (Finance)
- **Provider:** Frankfurter (ECB Data)
- **Base URL:** `https://api.frankfurter.dev/v1`
- **Verified GET Endpoint:** `GET /latest` (Query params: `base=EUR&symbols=USD%2CGBP%2CJPY`)
- **Live Test Result:** HTTP `200` in `0.181s` on `2026-11-22`
- **Documentation:** https://frankfurter.dev/
- **Free Access Evidence:** Open-source project (MIT) tracking ECB reference rates; official docs confirm free access with no API keys, registration, or usage fees.
- **Acceptance Rationale:** Returned live European Central Bank exchange rates (EUR to USD, GBP, JPY) in 0.181s. Open-source MIT project explicitly documented as free without API keys or registration.

#### U.S. Treasury Fiscal Data API (Finance)
- **Provider:** U.S. Department of the Treasury
- **Base URL:** `https://api.fiscaldata.treasury.gov/services/api/fiscal_service`
- **Verified GET Endpoint:** `GET /v2/accounting/od/debt_to_penny` (Query params: `page%5Bsize%5D=2&sort=-record_date`)
- **Live Test Result:** HTTP `200` in `0.61s` on `2026-11-22`
- **Documentation:** https://fiscaldata.treasury.gov/api-documentation/
- **Free Access Evidence:** Official U.S. Government public domain open data API; documentation explicitly states it is free with no API key or registration required.
- **Acceptance Rationale:** Official U.S. Department of the Treasury public domain API returning verified daily federal public debt records in 0.610s with no API key, registration, or usage fees.

#### Zippopotam.us Postal Code API (Geography)
- **Provider:** Zippopotam.us (GeoNames Data)
- **Base URL:** `https://api.zippopotam.us`
- **Verified GET Endpoint:** `GET /us/90210` (Query params: `None`)
- **Live Test Result:** HTTP `200` in `0.233s` on `2026-11-22`
- **Documentation:** https://api.zippopotam.us/
- **Free Access Evidence:** Open-source public service built on GeoNames data; official site confirms free access without API keys or registration.
- **Acceptance Rationale:** Returned structured postal code, city, state, and latitude/longitude data for US 90210 in 0.233s. Built on GeoNames open data and documented as free without keys or signup.

#### USGS Earthquake Hazards Program API (Science)
- **Provider:** U.S. Geological Survey
- **Base URL:** `https://earthquake.usgs.gov/fdsnws/event/1`
- **Verified GET Endpoint:** `GET /query` (Query params: `format=geojson&limit=2&minmagnitude=4.0`)
- **Live Test Result:** HTTP `200` in `0.508s` on `2026-11-22`
- **Documentation:** https://earthquake.usgs.gov/fdsnws/event/1/
- **Free Access Evidence:** U.S. Government public domain scientific web service; official documentation confirms free public access with no API key required.
- **Acceptance Rationale:** Official U.S. Geological Survey public domain seismic service returning live GeoJSON earthquake events (magnitude, place, timestamp, coordinates) in 0.508s with no authentication.

#### PubChem PUG REST API (Science)
- **Provider:** NIH / National Library of Medicine
- **Base URL:** `https://pubchem.ncbi.nlm.nih.gov/rest/pug`
- **Verified GET Endpoint:** `GET /compound/name/aspirin/property/MolecularFormula,MolecularWeight,IUPACName/JSON` (Query params: `None`)
- **Live Test Result:** HTTP `200` in `0.281s` on `2026-11-22`
- **Documentation:** https://pubchem.ncbi.nlm.nih.gov/docs/programmatic-access
- **Free Access Evidence:** Public U.S. National Institutes of Health database; official docs confirm free access without an API key under a fair-use limit of 5 requests/second.
- **Acceptance Rationale:** Official NIH / National Library of Medicine public database returning verified chemical compound data for aspirin (formula C9H8O4, molecular weight 180.16, IUPAC name) in 0.281s with no API key under a 5 req/sec fair-use policy.

#### Open Library Search API (Education)
- **Provider:** Internet Archive
- **Base URL:** `https://openlibrary.org`
- **Verified GET Endpoint:** `GET /search.json` (Query params: `q=python+programming&limit=2&fields=title%2Cauthor_name%2Cfirst_publish_year%2Cedition_count`)
- **Live Test Result:** HTTP `200` in `2.143s` on `2026-11-22`
- **Documentation:** https://openlibrary.org/developers/api
- **Free Access Evidence:** Non-profit Internet Archive project; official docs confirm read APIs are free with no API key required (descriptive User-Agent requested).
- **Acceptance Rationale:** Non-profit Internet Archive catalog returning real book titles, authors, publication years, and edition counts in 2.143s without an API key (descriptive User-Agent recommended).

#### Crossref REST API (Education)
- **Provider:** Crossref
- **Base URL:** `https://api.crossref.org`
- **Verified GET Endpoint:** `GET /works` (Query params: `query=machine+learning&rows=2&select=DOI%2Ctitle%2Cpublisher%2Ctype`)
- **Live Test Result:** HTTP `200` in `0.381s` on `2026-11-22`
- **Documentation:** https://api.crossref.org/swagger-ui/index.html
- **Free Access Evidence:** Non-profit scholarly infrastructure; official documentation confirms free public pool access with no API key or signup required.
- **Acceptance Rationale:** Non-profit scholarly metadata API returning real academic DOIs, publication titles, publishers, and work types in 0.381s via its free public pool with no API key required.

#### Forem API V1 (DEV.to) (Technology)
- **Provider:** Forem / DEV Community
- **Base URL:** `https://dev.to/api`
- **Verified GET Endpoint:** `GET /articles` (Query params: `tag=python&per_page=2`)
- **Live Test Result:** HTTP `200` in `0.295s` on `2026-11-22`
- **Documentation:** https://developers.forem.com/api/v1
- **Free Access Evidence:** Official Forem API v1 documentation explicitly marks GET /articles and GET /tags as public endpoints requiring no API key.
- **Acceptance Rationale:** Discovered during the APIs.guru scan; verified live GET /articles returns real published Python developer articles (titles, descriptions, authors, tags, reactions) in 0.295s, and Forem v1 docs explicitly mark read endpoints as public without an API key.

#### CIRCL Hashlookup API (Technology)
- **Provider:** CIRCL Luxembourg
- **Base URL:** `https://hashlookup.circl.lu`
- **Verified GET Endpoint:** `GET /lookup/md5/8ED4B4ED952526D89899E723F3488DE4` (Query params: `None`)
- **Live Test Result:** HTTP `200` in `0.163s` on `2026-11-22`
- **Documentation:** https://www.circl.lu/services/hashlookup/
- **Free Access Evidence:** Provided free of charge on a best-effort public basis by CIRCL under Creative Commons (CC-BY) terms with no authentication required.
- **Acceptance Rationale:** Discovered during the APIs.guru scan; verified live GET /lookup/md5/... returns real NIST NSRL software provenance metadata (filename, file size, product name, trust score) in 0.163s under CIRCL's free public CC-BY service.

#### PokéAPI (v2) (Entertainment)
- **Provider:** PokéAPI
- **Base URL:** `https://pokeapi.co/api/v2`
- **Verified GET Endpoint:** `GET /pokemon` (Query params: `limit=3&offset=0`)
- **Live Test Result:** HTTP `200` in `0.225s` on `2026-11-22`
- **Documentation:** https://pokeapi.co/docs/v2
- **Free Access Evidence:** Open-source project (BSD-3-Clause code); official docs confirm completely free read-only access with no API key under a fair-use caching policy.
- **Acceptance Rationale:** Well-known educational REST API (BSD-3-Clause code) returning clean paginated Pokémon resource listings in 0.225s with no API key required under a fair-use caching policy.

#### TVmaze API (Entertainment)
- **Provider:** TVmaze
- **Base URL:** `https://api.tvmaze.com`
- **Verified GET Endpoint:** `GET /search/shows` (Query params: `q=sherlock`)
- **Live Test Result:** HTTP `200` in `0.188s` on `2026-11-22`
- **Documentation:** https://www.tvmaze.com/api
- **Free Access Evidence:** Official docs state public endpoints are free with no API key required (rate limit ~20 req/10s) and data is licensed under CC BY-SA 4.0 with attribution.
- **Acceptance Rationale:** Returned structured TV show search results (title, genres, status, runtime, rating, network) in 0.188s. Official documentation confirms free keyless public endpoints under CC BY-SA 4.0 attribution terms.

#### APIs.guru OpenAPI Directory API (Open Data)
- **Provider:** APIs.guru
- **Base URL:** `https://api.apis.guru/v2`
- **Verified GET Endpoint:** `GET /metrics.json` (Query params: `None`)
- **Live Test Result:** HTTP `200` in `0.196s` on `2026-11-22`
- **Documentation:** https://apis.guru/api-doc/
- **Free Access Evidence:** Community-maintained open-source directory; API specifications and data are dedicated to the public domain under CC0 1.0 Universal with no auth required.
- **Acceptance Rationale:** Discovered during the APIs.guru scan; verified live GET /metrics.json returns real directory-wide API and endpoint counts (2,529 APIs, 3,992 specs, 108,837 endpoints) in 0.196s under CC0 1.0 public domain dedication.

#### World Bank Indicators API (v2) (Open Data)
- **Provider:** The World Bank
- **Base URL:** `https://api.worldbank.org/v2`
- **Verified GET Endpoint:** `GET /country/WLD/indicator/SP.POP.TOTL` (Query params: `format=json&per_page=2`)
- **Live Test Result:** HTTP `200` in `0.29s` on `2026-11-22`
- **Documentation:** https://datahelpdesk.worldbank.org/knowledgebase/topics/125589-developer-information
- **Free Access Evidence:** Official World Bank Open Data API; documentation confirms free public access with no API key required under the CC BY 4.0 license.
- **Acceptance Rationale:** Official World Bank Open Data API returning global population time-series records in 0.290s with no API key required under the CC BY 4.0 license.

## 3. Additional Verified Backups (Passed All Checks, Held Back to Keep Catalogue at 15)

- **Open-Meteo Geocoding API** (Geography, `https://geocoding-api.open-meteo.com/v1/search`) — HTTP `200` in `0.184s`. Verified free and keyless; omitted from the primary 15-item catalogue only to stay within the 10–15 target and avoid duplicate providers (`Open-Meteo`).
- **Spaceflight News API (v4)** (Science, `https://api.spaceflightnewsapi.net/v4/articles/`) — HTTP `200` in `0.55s`. Verified free and keyless; omitted from the primary 15-item catalogue only to stay within the 10–15 target.
- **Hacker News API** (Technology, `https://hacker-news.firebaseio.com/v0/item/8863.json`) — HTTP `200` in `0.326s`. Verified free and keyless; omitted from the primary 15-item catalogue only to stay within the 10–15 target.
- **Wikipedia REST API** (Open Data, `https://en.wikipedia.org/api/rest_v1/page/summary/Python_(programming_language)`) — HTTP `200` in `0.172s`. Verified free and keyless; omitted from the primary 15-item catalogue only to stay within the 10–15 target.

## 4. Rejected Candidates & Reasons

### A. Rejected from Phase 1 `WORKING_NO_AUTH` Scan (14 APIs)

| API Name | Provider | Rejection Reason |
| --- | --- | --- |
| ClearBlade API | `clearblade.com` | Only `/api/about` metadata returned HTTP 200 without auth; real IoT platform endpoints require user/device tokens and commercial accounts. |
| News Plugin | `freetv-app.com` | Points to a staging server (`staging2.freetv-app.com`) with no official public free-access documentation or clear usage terms. |
| HERE Tracking | `here.com:tracking` | Only the `/v2/health` health-check endpoint worked without auth; all tracking endpoints require Bearer tokens and HERE accounts. |
| TokenJay API services | `tokenjay.app` | Niche blockchain peer list with minimal public usage terms and unclear long-term public access documentation. |
| Contribly | `contribly.com` | Commercial OAuth2 platform with unclear free third-party usage terms and sparse public tag data. |
| ElevenLabs API Documentation | `elevenlabs.io` | Commercial paid AI voice service; only listing default voices worked unauthenticated, while all core audio synthesis endpoints require an API key and paid credits. |
| Clever-Cloud API | `clever-cloud.com` | Commercial cloud platform requiring OAuth for all real cloud operations; only a company blog feed endpoint responded without auth. |
| DRACOON API | `dracoon.team` | Only `/v4/public/time` (a server timestamp) worked without auth; core file-sharing API requires OAuth2 and paid accounts. |
| LanguageTool API | `languagetool.org` | GET `/v2/languages` only returns a static list of supported language codes, while actual grammar checking uses `POST /v2/check` with strict public rate limits. |
| Remote Settings PROD | `mozilla.com:kinto` | Root `/` only returns internal Firefox Kinto server metadata rather than a general-purpose public developer dataset. |
| MotaWord API | `motaword.com` | Root `/` only returns API info metadata; all translation endpoints require OAuth2 and paid translation credits. |
| BBC iPlayer Business Layer | `bbci.co.uk` | Only `/status` (health/status endpoint) worked without auth, and its documentation link points to an unofficial third-party blog post with no public usage terms. |
| NamSor API v2 | `namsor.com` | Only `/api2/json/apiStatus` (status check) worked without auth; actual name-classification endpoints require an API key and paid subscription. |
| Platform API (Ably) | `ably.io:platform` | Only `/time` (server timestamp) worked without auth; all messaging endpoints require Ably API keys. |

### B. Rejected from Phase 2 Curated Research (1 API)

- **REST Countries API (v3.1)** (`restcountries.com`) — **Rejected (Misleading HTTP 200 deprecation error & auth migration):** Returned HTTP `200` in `0.63s`, but the JSON payload contained `"success": false` with message `"This API version has been deprecated. Please visit https://restcountries.com/docs/countries/legacy-api-deprecation to migrate to our new version (v5)."` Version 5 requires an account and API key.

### C. Rejected from Phase 1 Non-Working Classifications (98 APIs)

- **`AUTH_REQUIRED` (44 APIs):** Rejected because endpoints returned HTTP `401`/`403`, returned a misleading HTTP `200` JSON auth error (`Swagger API2Cart`), or explicitly required API keys/OAuth2 in their OpenAPI specifications (e.g., OpenAI, Twitter API v2, Listen API, Clever, ShipEngine, Box, spoonacular, 1Password, Docker Hub, Google Abusive Experience Report, Fire Financial Services).
- **`UNAVAILABLE` (13 APIs):** Rejected due to DNS/connection failures, timeouts (`Transport for London`), HTTP `410 Gone` (`Meraki v0`), or HTTP `500` server errors (`Bungie.Net`).
- **`INCONCLUSIVE` (41 APIs):** Rejected due to HTTP `429` rate limits (`Medium API`), HTTP `400`/`404` responses (`QuickChart`, `balldontlie`, `Visual Crossing`), missing/template base URLs, or lack of testable parameter-free `GET` endpoints in the OpenAPI specification.

## 5. Limitations and Uncertainties

1. **Non-commercial or attribution clauses:** `Open-Meteo` is free for non-commercial/academic use (10,000 calls/day); `TVmaze`, `World Bank`, `Open-Meteo`, and `CIRCL Hashlookup` carry Creative Commons attribution terms (`CC BY` / `CC BY-SA`). All are well suited for a university project.
2. **Polite User-Agent header requirement:** `National Weather Service (NWS)` and `Open Library` request or require a descriptive `User-Agent` header; LOOKUPAPI's upcoming Test APIs module should include a standard `LOOKUPAPI` `User-Agent` header by default.
3. **Fair-use rate limits:** `PubChem` (5 req/s), `TVmaze` (~20 req/10s), `PokéAPI` (local caching fair-use policy), and `Crossref` (public pool rate limits) enforce fair-use throttling; automated rapid polling should be avoided.
4. **Point-in-time verification:** As demonstrated by `REST Countries v3.1` migrating to key-gated v5, public API providers can change endpoints or access terms over time. All 15 entries were verified live on `2026-11-22`, and LOOKUPAPI should continue handling HTTP errors and timeouts gracefully.
