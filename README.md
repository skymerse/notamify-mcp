# Notamify MCP Server

A Model Context Protocol (MCP) server that provides access to NOTAMs (Notice to Airmen) data through the Notamify API. This server allows LLMs to retrieve aviation notices, warnings, and operational information for airports worldwide.

## Features

- 🛩️ **NOTAM Retrieval** - Get active NOTAMs for specific airports
- 🕐 **Time Filtering** - Query NOTAMs for specific date/time ranges
- 🔍 **Search by ID** - Retrieve specific NOTAMs by their unique identifiers
- 📊 **Rich Interpretations** - Access AI-generated interpretations of NOTAM data
- 🌍 **Global Coverage** - Support for worldwide airports using ICAO codes
- 📄 **Pagination** - Handle large result sets automatically

## Installation

### Prerequisites

- Python 3.10 or higher
- Notamify API key ([get one here](https://api.notamify.com))

### Setup

1. **Install dependencies**:
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -r requirements.txt
   ```

2. **Configure API key**:
   ```bash
   cp env.example .env
   # Edit .env and add your API key:
   # NOTAMIFY_API_KEY=your_actual_api_key_here
   ```

3. **Make executable**:
   ```bash
   chmod +x notamify_server.py
   ```

## Usage

### Testing
```bash
# Test with MCP Inspector
uv run mcp dev notamify_server.py
```

### Claude Desktop Integration
```bash
# Install the server
uv run mcp install notamify_server.py --name "Notamify NOTAM Server"

# With environment variables
uv run mcp install notamify_server.py -v NOTAMIFY_API_KEY=your_key_here
```

## API Tools

### `get_notams`
Retrieve NOTAMs for specified airports and time periods.

**Parameters:**
- `locations` (required) - Comma-separated ICAO codes (max 5)
- `starts_at` (optional) - Start time in ISO 8601 format
- `ends_at` (optional) - End time in ISO 8601 format
- `hours_from_now` (optional) - Hours from current time (default: 24)

**Example:**
```
get_notams(locations="KJFK,EGLL", hours_from_now=48)
```

### `get_notams_by_ids`
Retrieve specific NOTAMs by their unique identifiers.

**Parameters:**
- `notam_ids` (required) - Comma-separated list of NOTAM IDs

### `generate_time_range`
Generate properly formatted timestamps for NOTAM queries.

**Parameters:**
- `hours_from_now` (optional) - Hours from current time (default: 24)

### `get_affected_elements`
Extract and display all affected elements from NOTAMs for specified airports.

**Parameters:**
- `locations` (required) - Comma-separated ICAO codes (max 5)
- `starts_at` (optional) - Start time in ISO 8601 format  
- `ends_at` (optional) - End time in ISO 8601 format
- `hours_from_now` (optional) - Hours from current time (default: 24)

**Returns:** Comprehensive summary including:
- Total NOTAMs and affected airports
- Categories of NOTAMs (runway, navigation, airspace, etc.)
- Specific affected elements with type, identifier, effect, and details
- Spatial elements with coordinates
- Flight planning recommendations

## Resources & Prompts

### Resources
- `notams://airports/{icao_codes}` - Get current NOTAMs for airports
- `config://api` - API configuration and usage limits

### Prompts
- `analyze_notams` - Generate structured NOTAM analysis for airports

## Examples

### Current NOTAMs
**Query:** "What are the current NOTAMs for JFK and Heathrow?"
```
get_notams(locations="KJFK,EGLL")
```

### Flight Planning Analysis
**Query:** "I'm flying to Munich tomorrow. What NOTAMs should I know about?"
```
get_affected_elements(locations="EDDM", hours_from_now=48)
```

### Common ICAO Codes
| Code | Airport | Location |
|------|---------|----------|
| KJFK | John F. Kennedy Intl | New York, USA |
| EGLL | London Heathrow | London, UK |
| EDDM | Munich Airport | Munich, Germany |
| KLAX | Los Angeles Intl | Los Angeles, USA |
| KORD | Chicago O'Hare | Chicago, USA |
| EDDF | Frankfurt Airport | Frankfurt, Germany |
| LFPG | Charles de Gaulle | Paris, France |
| EHAM | Amsterdam Schiphol | Amsterdam, Netherlands |

## Limitations

- **Maximum 5 ICAO codes** per request
- **Start date** cannot be earlier than 1 day before current UTC time
- **End date** must be later than start date
- **Page size** limited to 1-30 items per page
- ISO 8601 format required: `YYYY-MM-DDTHH:MM:SSZ`

## Development

### Running Tests
```bash
uv sync --group dev
uv run pytest
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

- **Notamify API Docs**: [api.notamify.com/docs](https://api.notamify.com/docs)
- **MCP Protocol**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Issues**: Report bugs via GitHub issues

## License

MIT License - see LICENSE file for details.

---

Built with [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) and [Notamify API](https://api.notamify.com) 