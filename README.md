# Notamify MCP Server

A Model Context Protocol (MCP) server that provides access to NOTAMs (Notice to Airmen) data through the Notamify API. It uses MCP Python SDK 2.x and negotiates the current `2026-07-28` MCP protocol with modern clients while retaining SDK-level compatibility with earlier protocol revisions.

## Features

- 🛩️ **NOTAM Retrieval** - Get active NOTAMs for specific airports
- 🕐 **Time Filtering** - Query NOTAMs for specific date/time ranges
- 📊 **Rich Interpretations** - Access AI-generated interpretations of NOTAM data
- 🌍 **Global Coverage** - Support for worldwide airports using ICAO codes
- 📄 **Pagination** - Handle large result sets automatically

## Installation

### Prerequisites

- Python 3.10 or higher
- Notamify API key ([get one here](https://api.notamify.com))

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/skymerse/notamify-mcp.git
   cd notamify-mcp
   ```


2. **Install dependencies**:
   ```bash
   # Using uv (recommended)
   uv sync

   # Or using pip
   pip install -e .
   ```

3. **Configure the API key**:
   ```bash
   export NOTAMIFY_API_KEY=your_actual_api_key_here
   ```

   Keep the key in your environment or your MCP host's secret configuration. Do not commit it to the repository.

4. **Make executable**:
   ```bash
   chmod +x notamify_server.py
   ```

## Usage

### Claude Desktop Integration
```bash
# Install the server
uv run mcp install notamify_server.py --name "Notamify NOTAM Server"

# With environment variables, if not set previously
uv run mcp install notamify_server.py -v NOTAMIFY_API_KEY=your_key_here
```

### Development and MCP Inspector

```bash
# Start the MCP Inspector against the local server
uv run mcp dev notamify_server.py

# Run the stdio server directly
uv run mcp run notamify_server.py

# Or use the installed console command
uv run notamify-mcp
```

## API Tools

### `get_notams`
Retrieve NOTAMs for specified airports and time periods.

**Parameters:**
- `locations` (required) - JSON list of ICAO codes (max 5)
- `starts_at` (optional) - Start time in ISO 8601 format
- `ends_at` (optional) - End time in ISO 8601 format
- `hours_from_now` (optional) - Hours from current time (default: 24)

**Example:**
```
get_notams(locations=["KJFK", "EGLL"], hours_from_now=48)
```

### `get_affected_elements`
Extract and display all affected elements from NOTAMs for specified airports.

**Parameters:**
- `locations` (required) - JSON list of ICAO codes (max 5)
- `starts_at` (optional) - Start time in ISO 8601 format  
- `ends_at` (optional) - End time in ISO 8601 format
- `hours_from_now` (optional) - Hours from current time (default: 24)

**Returns:** A comprehensive summary including:
- Total NOTAMs and affected airports
- Categories of NOTAMs (runway, navigation, airspace, etc.)
- Specific affected elements with type, identifier, effect, and details
- Spatial elements with coordinates
- Flight planning recommendations

## Resources & Prompts

### Resources
- `config://api` - API configuration and usage limits

### Prompts
- `analyze_notams` - Generate structured NOTAM analysis for airports

## Examples

### Current NOTAMs
**Query:** "What are the current NOTAMs for JFK and Heathrow?"
```
get_notams(locations=["KJFK", "EGLL"])
```

### Flight Planning Analysis
**Query:** "I'm flying to Munich tomorrow. What NOTAMs should I know about?"
```
get_affected_elements(locations=["EDDM"], hours_from_now=48)
```

## Limitations

- **Maximum 5 ICAO codes** per request
- **Start date** cannot be earlier than 1 day before current UTC time
- **End date** must be later than start date
- **Page size** limited to 1-30 items per page
- ISO 8601 format required: `YYYY-MM-DDTHH:MM:SSZ`

## Development

### Running Tests
```bash
uv sync --all-groups

# Unit, API-client, and in-memory MCP protocol tests
uv run pytest -m "not live"

# Optional real Notamify API test (may consume API credits)
NOTAMIFY_API_KEY=your_key_here uv run pytest -m live
```

The protocol tests connect both through the SDK's in-memory `Client` and a real stdio subprocess, verify negotiation of MCP `2026-07-28`, check server identity and capabilities, and exercise both tools, the resource, and the prompt end to end.

### Contributing
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

- **Notamify API Docs**: [api.notamify.com/docs](https://api.notamify.com/docs)
- **MCP Protocol (latest)**: [modelcontextprotocol.io/specification/latest](https://modelcontextprotocol.io/specification/latest)
- **MCP Python SDK v2**: [py.sdk.modelcontextprotocol.io](https://py.sdk.modelcontextprotocol.io/)
- **Issues**: Report bugs via GitHub issues

## License

MIT License - see LICENSE file for details.

---

Built with [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) and [Notamify API](https://api.notamify.com)
