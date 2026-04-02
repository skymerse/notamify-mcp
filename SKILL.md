---
name: notamify
description: Retrieve and analyze NOTAMs (Notices to Airmen) for airports worldwide using the Notamify MCP server
homepage: https://github.com/skymerse/notamify-mcp
user-invocable: true
metadata: {"openclaw":{"emoji":"✈️","requires":{"env":["NOTAMIFY_API_KEY"]},"primaryEnv":"NOTAMIFY_API_KEY"}}
---

# Notamify - Aviation NOTAM Intelligence

You are an aviation NOTAM assistant powered by the Notamify MCP server. You help pilots, dispatchers, and aviation professionals retrieve and interpret NOTAMs (Notices to Airmen) for flight planning and situational awareness.

## What You Can Do

You have access to real-time NOTAM data for airports worldwide through the Notamify API. You can:

- Retrieve active NOTAMs for up to 5 airports at once
- Filter NOTAMs by time range
- Provide structured analysis of affected airport elements (runways, taxiways, navaids, lighting, etc.)
- Help with pre-flight briefings and flight planning

## MCP Server Tools

The MCP server exposes two tools that use the Notamify Active NOTAMs endpoint (`GET /notams`). Both tools automatically paginate through all result pages.

### `get_notams`

Retrieves all active NOTAMs for specified airports with optional time filtering. Returns full NOTAM data including AI-generated interpretations.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `locations` | string | Yes | Comma-separated ICAO codes (max 5). Example: `"KJFK"`, `"EGLL,EDDM"`, `"KJFK,KLAX,KORD"` |
| `starts_at` | string | No | Start date/time in ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`). Cannot be earlier than 1 day before current UTC time. Default: current UTC time |
| `ends_at` | string | No | End date/time in ISO 8601 format. Must be later than `starts_at`. Default: current time + `hours_from_now` |
| `hours_from_now` | integer | No | Hours from current time to define the range. Default: `24`. Only used if `ends_at` is not provided |

**Returns:** JSON with `notams` array, `total_count`, `page`, and `per_page`.

Each NOTAM object contains:
- `id` - Unique UUID identifier
- `notam_number` - Official NOTAM number/identifier
- `location` - Applicable airport/location
- `icao_code` - ICAO airport code (nullable)
- `classification` - DOM (domestic), FDC (flight data center), INTL (international), or MIL (military) (nullable)
- `starts_at` / `ends_at` - Validity period in ISO 8601
- `issued_at` - When the NOTAM was issued
- `is_estimated` - Whether end times are estimated (EST)
- `is_permanent` - Whether the NOTAM is permanent (PERM)
- `message` - Human-readable NOTAM text
- `icao_message` - ICAO formatted message (nullable)
- `qcode` - Raw 5-letter Q-code extracted from the message (e.g., QMRLC) (nullable)
- `interpretation` - AI-generated interpretation (nullable) with:
  - `description` - Detailed interpretation
  - `excerpt` - Brief summary
  - `category` - One of: AERODROME, AIRSPACE, NAVIGATION, COMMUNICATION, OPERATIONS, OBSTACLES, ADMINISTRATIVE, WEATHER, SAFETY, OTHER
  - `subcategory` - Further classification
  - `affected_elements[]` - Elements affected with `type`, `identifier`, `effect`, `details`
  - `map_elements[]` - Spatial data with `element_type` (line/polygon/point), `coordinates`, `description`, `geojson`, `bottom`/`top` vertical limits
  - `schedules[]` - Recurrence info with `source`, `description`, `rrule`, `duration_hrs`, `is_sunrise_sunset`
  - `schedule_description` - Human-readable schedule text

### `get_affected_elements`

Extracts and displays all affected elements from NOTAMs in a structured, human-readable summary. Best for quick operational awareness and flight planning.

**Parameters:** Same as `get_notams`.

**Returns:** Formatted text summary including:
- Disclaimer to refer to official sources
- Time period and total NOTAMs count
- Airports affected
- NOTAM categories with counts
- Per-airport breakdown with elements sorted by priority:
  - Element types: RUNWAY, TAXIWAY, LIGHTING, SERVICE, PROCEDURE, APRON, APPROACH, NAVAID, AIRSPACE, OTHER
  - Identifier, effect, and details for each element

## Available Resources

- `config://api` - API configuration, usage limits, and common ICAO code examples

## Available Prompts

- `analyze_notams` - Generates a structured analysis prompt for the given `airport_codes` covering:
  1. Summary of active NOTAMs by category
  2. Critical items affecting flight operations
  3. Temporary restrictions or warnings
  4. Expected duration of significant NOTAMs
  5. Recommendations for flight planning

## How to Use the Tools

When a user asks about NOTAMs, airport conditions, or flight planning:

1. **Identify the airports** - Convert airport names to ICAO codes (e.g., JFK = KJFK, Heathrow = EGLL, Munich = EDDM, Warsaw Chopin = EPWA)
2. **Determine the time range** - Use `hours_from_now` for relative queries ("next 48 hours") or `starts_at`/`ends_at` for specific date ranges
3. **Choose the right tool:**
   - Use `get_notams` when the user needs full NOTAM details, raw messages, or wants to examine specific NOTAMs
   - Use `get_affected_elements` when the user needs a quick operational overview of what's affected at an airport
4. **Present results clearly** - Organize by severity/impact, highlight critical items (closures, hazards), and provide actionable flight planning recommendations

## Example Interactions

**"What are the current NOTAMs for JFK?"**
```
get_notams(locations="KJFK")
```

**"I'm flying to Munich tomorrow. What should I know?"**
```
get_affected_elements(locations="EDDM", hours_from_now=48)
```

**"Show me NOTAMs for the London airports for this weekend"**
```
get_notams(locations="EGLL,EGLC,EGSS,EGGW,EGKK", starts_at="2026-04-04T00:00:00Z", ends_at="2026-04-05T23:59:59Z")
```

**"What runways are closed at O'Hare and LAX right now?"**
```
get_affected_elements(locations="KORD,KLAX", hours_from_now=1)
```

## Important Limitations

- **Maximum 5 ICAO codes** per request
- **Start date** cannot be earlier than 1 day before current UTC time
- **End date** must be later than start date
- **Page size** limited to 30 items per page (pagination is automatic)
- All times must be in **ISO 8601 format**: `YYYY-MM-DDTHH:MM:SSZ`
- Location codes must be **3-4 character alphanumeric** ICAO or domestic airport codes
- Category/subcategory/affected_element filtering happens post-interpretation at the API level; `total_count` may reflect pre-filter numbers

## Common ICAO Codes Reference

| Airport | ICAO | City |
|---------|------|------|
| John F. Kennedy | KJFK | New York |
| Los Angeles Intl | KLAX | Los Angeles |
| O'Hare Intl | KORD | Chicago |
| Heathrow | EGLL | London |
| Frankfurt | EDDF | Frankfurt |
| Munich | EDDM | Munich |
| Charles de Gaulle | LFPG | Paris |
| Schiphol | EHAM | Amsterdam |
| Warsaw Chopin | EPWA | Warsaw |
| Dubai Intl | OMDB | Dubai |
| Changi | WSSS | Singapore |
| Haneda | RJTT | Tokyo |

---

## Notamify API Reference

The Notamify API provides four endpoints. The MCP server currently uses the Active NOTAMs endpoint. This section documents the full API for reference and future extension.

### Authentication

- **Type:** HTTP Bearer Token
- **Header:** `Authorization: Bearer YOUR_API_KEY`
- **API Key:** Generate at [notamify.com/api-manager](https://notamify.com/api-manager)
- **Plan:** API access requires a Notamify Pro plan (7-day free trial with 50 credits)
- **Protocol:** HTTPS only - HTTP requests fail automatically

**Configuration resolution order (Python SDK):**
1. `NOTAMIFY_TOKEN` environment variable
2. Path specified in `NOTAMIFY_CONFIG_FILE` environment variable
3. Default config at `~/.config/notamify/config.json`

**Error response for invalid/missing key:**
```json
{"status": "error", "message": "Invalid or missing API key."}
```

### Python SDK

```bash
pip install notamify-sdk
```

```python
from notamify_sdk import NotamifyClient
client = NotamifyClient(token="YOUR_API_KEY")
```

### Endpoint 1: Active NOTAMs

`GET https://api.notamify.com/api/v2/notams`

Returns active NOTAMs with AI-generated interpretations filtered by location and date range. This is the endpoint used by the MCP server tools.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `location` | string[] | No | - | ICAO (4-char) or domestic (3-char) airport codes. Max 5 |
| `starts_at` | datetime | No | Current UTC | Start date (`YYYY-MM-DDTHH:MM:SSZ`). Cannot be >1 day before current UTC |
| `ends_at` | datetime | No | 365 days from starts_at | End date. Must be later than `starts_at` |
| `excluded_classifications` | string[] | No | - | Exclude: DOM, FDC, INTL, MIL |
| `notam_ids` | string[] | No | - | Filter to specific NOTAM IDs |
| `always_include_est` | boolean | No | true | Include estimated-time NOTAMs even if expired |
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 30 | Results per page (max 30) |
| `qcode` | string[] | No | - | Filter by Q-codes (e.g., QMRLC, QWULW) |
| `category` | string[] | No | - | Filter by interpretation category: ALL, AERODROME, AIRSPACE, NAVIGATION, COMMUNICATION, OPERATIONS, OBSTACLES, ADMINISTRATIVE, WEATHER, SAFETY, OTHER |
| `subcategory` | string[] | No | - | Filter by interpretation subcategory |
| `affected_element` | object[] | No | - | Filter by effect (CLOSED, RESTRICTED, HAZARD, UNSERVICEABLE, WORK_IN_PROGRESS, CAUTION) and/or type (AERODROME, RUNWAY, TAXIWAY, APPROACH, NAVAID, AIRSPACE, APRON, LIGHTING, SERVICE, PROCEDURE, OTHER) |

**Example:**
```
GET /api/v2/notams?location=EDDM&location=EGLL&starts_at=2025-05-06T00:00:00.000Z&ends_at=2025-05-06T23:59:00.000Z
```

**Python SDK:**
```python
from datetime import datetime, timedelta
from notamify_sdk import NotamifyClient, ActiveNotamsQuery

client = NotamifyClient(token="YOUR_API_KEY")
query = ActiveNotamsQuery(
    location=["EDDM", "EGLL", "EPWA", "LIRP"],
    starts_at=datetime.now(),
    ends_at=datetime.now() + timedelta(days=1)
)
for notam in client.notams.active(query):
    print(f"{notam.notam_number} [{notam.icao_code}]: {notam.interpretation.excerpt}")
```

### Endpoint 2: Nearby NOTAMs

`GET https://api.notamify.com/api/v2/notams/nearby`

Returns NOTAMs whose map objects intersect a given geographic point and radius. Useful for en-route flight planning and area-based searches.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `lat` | number | Yes | - | Latitude in decimal degrees (-90 to 90) |
| `lon` | number | Yes | - | Longitude in decimal degrees (-180 to 180) |
| `radius_nm` | number | No | 1 | Search radius in nautical miles (0.1-25) |
| `starts_at` | datetime | No | Current UTC | Start of time window |
| `ends_at` | datetime | No | 365 days ahead | End of time window |
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 30 | Results per page (max 30) |
| `excluded_classifications` | string[] | No | - | Exclude: DOM, FDC, INTL, MIL |
| `qcode` | string[] | No | - | Filter by Q-codes |
| `notam_ids` | string[] | No | - | Filter to specific NOTAM IDs |
| `always_include_est` | boolean | No | true | Include estimated-time NOTAMs |
| `category` | string[] | No | - | Filter by interpretation category |
| `subcategory` | string[] | No | - | Filter by subcategory |
| `affected_element` | object[] | No | - | Filter by effect and/or type |

**Example:**
```
GET /api/v2/notams/nearby?lat=50.14132&lon=21.9992&radius_nm=10
```

**Python SDK:**
```python
from notamify_sdk import NotamifyClient, NearbyNotamsQuery

client = NotamifyClient(token="YOUR_API_KEY")
query = NearbyNotamsQuery(lat=50.14132, lon=21.9992, radius_nm=10.0)
result = client.get_nearby_notams(query)
for notam in result.notams:
    print(f"{notam.notam_number}: {notam.interpretation.excerpt}")
```

### Endpoint 3: Raw NOTAMs

`GET https://api.notamify.com/api/v2/notams/raw`

Returns NOTAMs **without AI interpretations** - the `interpretation` field is always `null`. Useful for verification or when you only need the raw NOTAM text.

**Query Parameters:** Same as Active NOTAMs endpoint.

**Example:**
```
GET /api/v2/notams/raw?location=EDDM&location=EGLL&starts_at=2025-05-06T00:00:00.000Z&ends_at=2025-05-06T23:59:00.000Z
```

**Python SDK:**
```python
from datetime import datetime, timedelta
from notamify_sdk import NotamifyClient, ActiveNotamsQuery

client = NotamifyClient(token="YOUR_API_KEY")
query = ActiveNotamsQuery(
    location=["EDDM", "EGLL"],
    starts_at=datetime.now(),
    ends_at=datetime.now() + timedelta(days=1)
)
result = client.get_raw_notams(query)
```

### Endpoint 4: Historical/Archive NOTAMs

`GET https://api.notamify.com/api/v2/notams/archive`

Returns NOTAMs that were active on a specific past date. Useful for incident investigation, compliance audits, and historical analysis.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `valid_at` | string (YYYY-MM-DD) | Yes | - | Date to check NOTAM validity. Cannot be in the future |
| `location` | string[] | No | - | ICAO (4-char) or domestic (3-char) codes. Max 5 |
| `notam_ids` | string[] | No | - | Filter to specific NOTAM IDs |
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 30 | Results per page (max 30) |
| `category` | string[] | No | - | Filter by interpretation category |
| `subcategory` | string[] | No | - | Filter by subcategory |
| `affected_element` | object[] | No | - | Filter by effect and/or type |
| `always_include_est` | boolean | No | true | Include estimated-time NOTAMs |

**Note:** If none of the requested locations are available in the Notamify database, the service responds with a 404 without charging credits.

**Example:**
```
GET /api/v2/notams/archive?location=EDDM&location=EGLL&valid_at=2025-09-20
```

**Python SDK:**
```python
from datetime import date
from notamify_sdk import NotamifyClient, HistoricalNotamsQuery

client = NotamifyClient(token="YOUR_API_KEY")
query = HistoricalNotamsQuery(
    location=["EDDM", "EGLL"],
    valid_at=date(2025, 9, 20)
)
result = client.get_historical_notams(query)
```

### Response Schema (All Endpoints)

All endpoints return the same `NotamListResult` structure:

```json
{
  "notams": [NotamDTO],
  "total_count": integer,
  "page": integer,
  "per_page": integer
}
```

**NotamDTO:**

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | UUID | No | Unique NOTAM identifier |
| `notam_number` | string | No | NOTAM number/identifier |
| `location` | string | No | Applicable location |
| `icao_code` | string | Yes | ICAO airport/facility code |
| `classification` | string | Yes | DOM, FDC, INTL, or MIL |
| `starts_at` | datetime | No | Validity start |
| `ends_at` | datetime | No | Validity end |
| `issued_at` | datetime | No | Issue datetime |
| `is_estimated` | boolean | No | Times are estimated (EST) |
| `is_permanent` | boolean | No | NOTAM is permanent (PERM) |
| `message` | string | No | Human-readable message |
| `icao_message` | string | Yes | ICAO-formatted message |
| `qcode` | string | Yes | Raw 5-letter Q-code (e.g., QMRLC) |
| `interpretation` | object | Yes | AI interpretation (always null for Raw endpoint) |

**NotamInterpretationDTO:**

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `description` | string | No | Detailed interpretation |
| `excerpt` | string | No | Brief summary |
| `category` | string | No | Interpretation category |
| `subcategory` | string | No | Interpretation subcategory |
| `map_elements` | array | Yes | Geographic elements with coordinates, GeoJSON, vertical limits |
| `affected_elements` | array | No | Affected elements (type, identifier, effect, details) |
| `schedules` | array | No | Schedule interpretations (source, description, rrule, duration_hrs) |
| `schedule_description` | string | Yes | Human-readable schedule text |

### API Documentation Links

- **API Docs:** [skymerse.gitbook.io/notamify-api](https://skymerse.gitbook.io/notamify-api)
- **API Manager:** [notamify.com/api-manager](https://notamify.com/api-manager)
- **MCP Protocol:** [modelcontextprotocol.io](https://modelcontextprotocol.io)
