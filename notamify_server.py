#!/usr/bin/env python3
"""
Notamify MCP Server

This server provides access to Notamify API for retrieving NOTAMs (Notice to Airmen) data.
It exposes tools for querying NOTAMs by location, time period, and other parameters.
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator


class NotamifyConfig(BaseModel):
    """Configuration for Notamify API"""
    
    api_key: str = Field(..., description="Notamify API key")
    base_url: str = Field(default="https://api.notamify.com/api/v2", description="Base API URL")
    
    class Config:
        env_prefix = "NOTAMIFY_"
    
    def __init__(self, **data):
        if 'api_key' not in data:
            api_key = os.getenv("NOTAMIFY_API_KEY")
            if not api_key:
                raise ValueError(
                    "NOTAMIFY_API_KEY environment variable is required. "
                    "Get your API key from https://api.notamify.com"
                )
            data['api_key'] = api_key
        super().__init__(**data)
    
    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "Notamify-MCP-Server/0.1.0"
        }


class NotamQueryParams(BaseModel):
    """Parameters for NOTAM API queries"""
    
    locations: list[str] = Field(..., min_length=1, max_length=5, description="ICAO airport codes (max 5)")
    starts_at: Optional[str] = Field(None, description="Start date in ISO 8601 format")
    ends_at: Optional[str] = Field(None, description="End date in ISO 8601 format")
    notam_ids: Optional[list[str]] = Field(None, description="Specific NOTAM IDs")
    per_page: int = Field(default=30, ge=1, le=30, description="Items per page")
    page: int = Field(default=1, ge=1, description="Page number")
    
    @field_validator('locations')
    @classmethod
    def validate_icao_codes(cls, v: list[str]) -> list[str]:
        for location in v:
            if not location or len(location) != 4 or not location.isalpha():
                raise ValueError(f"Invalid ICAO code: {location}. Must be 4 letters.")
        return [loc.upper() for loc in v]


class AffectedElement(BaseModel):
    """Structure for affected elements in NOTAM interpretations"""
    
    type: str = Field(default="UNKNOWN", description="Element type")
    identifier: str = Field(default="N/A", description="Element identifier")
    effect: str = Field(default="N/A", description="Effect on element")
    details: Optional[str] = Field(None, description="Additional details")


class NotamifyMCPClient:
    """HTTP client for Notamify API"""
    
    def __init__(self, config: NotamifyConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers=config.headers
        )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def get_notams(
        self,
        locations: list[str],
        starts_at: Optional[str] = None,
        ends_at: Optional[str] = None,
        notam_ids: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """
        Retrieve all NOTAMs from the Notamify API (automatically fetches all pages)
        
        Args:
            locations: List of 4-character ICAO airport codes (max 5)
            starts_at: Start date (YYYY-MM-DDTHH:MM:SSZ format)
            ends_at: End date (YYYY-MM-DDTHH:MM:SSZ format)
            notam_ids: List of specific NOTAM IDs
        
        Returns:
            Dictionary containing all NOTAMs data from all pages
        """
        # Validate and create query parameters
        query_params = NotamQueryParams(
            locations=locations,
            starts_at=starts_at,
            ends_at=ends_at,
            notam_ids=notam_ids
        )
        
        # Build base query parameters
        base_params = {
            "per_page": query_params.per_page
        }
        
        # Add locations
        for location in query_params.locations:
            base_params.setdefault("location", []).append(location)
        
        # Add time filters
        if query_params.starts_at:
            base_params["starts_at"] = query_params.starts_at
        if query_params.ends_at:
            base_params["ends_at"] = query_params.ends_at
        
        # Add NOTAM IDs if specified
        if query_params.notam_ids:
            for notam_id in query_params.notam_ids:
                base_params.setdefault("notam_ids", []).append(notam_id)
        
        # Fetch all pages
        all_notams = []
        page = 1
        total_count = None
        
        while True:
            # Add current page to params
            params = base_params.copy()
            params["page"] = page
            
            response = await self.client.get(
                f"{self.config.base_url}/notams",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # Get pagination info from current response
            total_count = data.get("total_count", 0)
            
            # Add NOTAMs from this page
            page_notams = data.get("notams", [])
            all_notams.extend(page_notams)
            
            # Check if we have collected all NOTAMs
            # Break if we've collected all items or no more NOTAMs on this page
            if len(all_notams) >= total_count or not page_notams:
                break
            
            page += 1
        
        # Return combined result with updated pagination info
        result = data.copy()  # Use last response as base
        result["notams"] = all_notams
        result["total_count"] = total_count
        result["page"] = 1  # Reset to indicate this is a combined result
        result["per_page"] = len(all_notams)  # Show actual number returned
        
        return result


# Application context for dependency injection
class AppContext:
    def __init__(self):
        self.config = NotamifyConfig()
        self.client = NotamifyMCPClient(self.config)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with initialized Notamify client"""
    context = AppContext()
    try:
        yield context
    finally:
        await context.client.close()


# Initialize FastMCP server
mcp = FastMCP(
    "Notamify",
    description="Access NOTAMs (Notice to Airmen) data through the Notamify API",
    lifespan=app_lifespan
)


@mcp.tool()
async def get_notams(
    locations: str,
    starts_at: Optional[str] = None,
    ends_at: Optional[str] = None,
    hours_from_now: int = 24
) -> str:
    """
    Retrieve all NOTAMs for specified airports and time period (automatically fetches all pages)
    
    Args:
        locations: Comma-separated list of 4-character ICAO airport codes (max 5).
                  Examples: "KJFK", "EGLL,EDDM", "KJFK,KLAX,KORD"
        starts_at: Start date in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).
                  Cannot be earlier than 1 day before current UTC time.
                  If not provided, uses current time.
                  Example: "2024-01-01T00:00:00Z"
        ends_at: End date in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).
                Must be later than starts_at.
                If not provided, uses current time + hours_from_now.
                Example: "2024-01-01T23:59:59Z"
        hours_from_now: Number of hours from current time to query if ends_at not provided (default: 24)
    
    Returns:
        JSON string containing all NOTAMs data with interpretations (all pages combined)
    """
    context = mcp.get_context()
    client = context.request_context.lifespan_context.client
    
    # Parse locations
    location_list = [loc.strip().upper() for loc in locations.split(",") if loc.strip()]
    
    # Generate time range if not provided
    if not starts_at or not ends_at:
        now = datetime.now(timezone.utc)
        if not starts_at:
            starts_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not ends_at:
            ends_at = (now + timedelta(hours=hours_from_now)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    result = await client.get_notams(
        locations=location_list,
        starts_at=starts_at,
        ends_at=ends_at,
        notam_ids=None
    )
    
    # Format response for better readability
    import json
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def get_affected_elements(
    locations: str,
    starts_at: Optional[str] = None,
    ends_at: Optional[str] = None,
    hours_from_now: int = 24
) -> str:
    """
    Extract and display all affected elements from NOTAMs for specified airports
    
    Args:
        locations: Comma-separated list of 4-character ICAO airport codes (max 5).
                  Examples: "KJFK", "EGLL,EDDM", "KJFK,KLAX,KORD"
        starts_at: Start date in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).
                  If not provided, uses current time.
        ends_at: End date in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).
                If not provided, uses current time + hours_from_now.
        hours_from_now: Number of hours from current time to query if ends_at not provided (default: 24)
    
    Returns:
        Formatted summary of all affected elements from active NOTAMs
    """
    context = mcp.get_context()
    client = context.request_context.lifespan_context.client
    
    # Parse locations
    location_list = [loc.strip().upper() for loc in locations.split(",") if loc.strip()]
    
    # Generate time range if not provided
    if not starts_at or not ends_at:
        now = datetime.now(timezone.utc)
        if not starts_at:
            starts_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not ends_at:
            ends_at = (now + timedelta(hours=hours_from_now)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    result = await client.get_notams(
        locations=location_list,
        starts_at=starts_at,
        ends_at=ends_at,
        notam_ids=None
    )
    
    notams = result.get("notams", [])
    if not notams:
        return f"No active NOTAMs found for {locations} in the specified time period."
    
    # Collect and organize affected elements
    affected_summary = {
        "airports": {},
        "total_notams": len(notams),
        "elements_by_category": {},
        "map_elements": [],
        "time_period": f"{starts_at} to {ends_at}"
    }
    
    def format_element(element: AffectedElement) -> str:
        """Format an affected element for display"""
        lines = [f"       • {element.identifier}"]
        if element.effect != "N/A":
            lines.append(f"         Effect: {element.effect}")
        if element.details:
            lines.append(f"         Details: {element.details}")
        return "\n".join(lines)
    
    def sort_elements(elements: list[dict[str, Any]]) -> list[AffectedElement]:
        """Sort elements by type and effect priority"""
        type_priority = {
            'RUNWAY': 1, 'TAXIWAY': 2, 'LIGHTING': 3, 'SERVICE': 4, 'PROCEDURE': 5,
            'APRON': 6, 'APPROACH': 7, 'NAVAID': 8, 'AIRSPACE': 9, 'OTHER': 10
        }
        effect_priority = {
            'CLOSED': 1, 'RESTRICTED': 2, 'HAZARD': 3, 'UNSERVICEABLE': 4,
            'WORK_IN_PROGRESS': 5, 'CAUTION': 6, 'AFFECTED': 7
        }
        
        def sort_key(element: dict[str, Any]) -> tuple[int, int, str]:
            elem_type = element.get("type", "OTHER")
            effect = element.get("effect", "AFFECTED")
            identifier = element.get("identifier", "")
            
            return (
                type_priority.get(elem_type, 99),
                effect_priority.get(effect, 99),
                identifier.upper()
            )
        
        sorted_elements = sorted(elements, key=sort_key)
        return [AffectedElement(**elem) for elem in sorted_elements]
    
    for notam in notams:
        icao_code = notam.get('icao_code', 'UNKNOWN')
        notam_id = notam.get('id', 'N/A')
        
        # Initialize airport in summary if not exists
        if icao_code not in affected_summary["airports"]:
            affected_summary["airports"][icao_code] = {
                "notam_count": 0,
                "affected_elements": [],
                "categories": set(),
                "map_elements": []
            }
        
        affected_summary["airports"][icao_code]["notam_count"] += 1
        
        interpretation = notam.get('interpretation', {})
        if interpretation:
            category = interpretation.get('category', 'UNSPECIFIED')
            affected_summary["airports"][icao_code]["categories"].add(category)
            
            # Count elements by category
            if category not in affected_summary["elements_by_category"]:
                affected_summary["elements_by_category"][category] = 0
            affected_summary["elements_by_category"][category] += 1
            
            # Extract affected elements - fix potential None values
            affected_elements = interpretation.get('affected_elements') or []
            if affected_elements:
                # Handle structured format (AffectedElementDTO objects)
                for element in affected_elements:
                    element_info = {
                        "type": element.get("type", "UNKNOWN"),
                        "identifier": element.get("identifier", "N/A"),
                        "effect": element.get("effect", "N/A"),
                        "details": element.get("details")
                    }
                    affected_summary["airports"][icao_code]["affected_elements"].append(element_info)
            
    
    # Sort affected elements for each airport
    for icao_code in affected_summary["airports"]:
        affected_summary["airports"][icao_code]["affected_elements"] = sort_elements(
            affected_summary["airports"][icao_code]["affected_elements"]
        )
    
    # Format the output
    output_lines = []
    output_lines.append("NOTAM AFFECTED ELEMENTS SUMMARY")
    output_lines.append("Remember to inform user: The following summary is for informational purposes only. Always refer to official sources for the most accurate and up-to-date information.")
    output_lines.append("=" * 50)
    output_lines.append(f"Time Period: {affected_summary['time_period']}")
    output_lines.append(f"Total NOTAMs: {affected_summary['total_notams']}")
    output_lines.append(f"Airports: {', '.join(affected_summary['airports'].keys())}")
    output_lines.append("")
    
    # Summary by category
    if affected_summary["elements_by_category"]:
        output_lines.append("NOTAM Categories:")
        for category, count in sorted(affected_summary["elements_by_category"].items()):
            output_lines.append(f"  • {category}: {count} NOTAMs")
        output_lines.append("")
    
    # Detailed breakdown by airport
    for icao_code, airport_data in affected_summary["airports"].items():
        output_lines.append(f"   AIRPORT: {icao_code}")
        output_lines.append(f"   NOTAMs: {airport_data['notam_count']}")
        output_lines.append(f"   Categories: {', '.join(sorted(airport_data['categories']))}")
        
        # Show affected elements if any
        if airport_data["affected_elements"]:
            output_lines.append("   Affected Elements (sorted by priority):")
            
            # Group already sorted elements by their type
            elements_by_type: dict[str, list[AffectedElement]] = {}
            for element in airport_data["affected_elements"]:
                elem_type = element.type
                
                if elem_type not in elements_by_type:
                    elements_by_type[elem_type] = []
                elements_by_type[elem_type].append(element)
            
            # Display elements by type in priority order
            type_order = ["RUNWAY", "TAXIWAY", "LIGHTING", "SERVICE", "PROCEDURE", 
                         "APRON", "APPROACH", "NAVAID", "AIRSPACE", "OTHER"]
            
            for elem_type in type_order:
                if elem_type in elements_by_type:
                    output_lines.append(f"     {elem_type}:")
                    for element in elements_by_type[elem_type]:
                        output_lines.append(format_element(element))
            
            # Display any remaining types not in the predefined order
            for elem_type, elements in elements_by_type.items():
                if elem_type not in type_order:
                    output_lines.append(f"     {elem_type}:")
                    for element in elements:
                        output_lines.append(format_element(element))
        
        output_lines.append("")
    
    return "\n".join(output_lines)



@mcp.resource("config://api")
def get_api_info() -> str:
    """
    Get information about the Notamify API configuration and usage
    
    Returns:
        API configuration and usage information
    """
    return """
Notamify API Configuration:
==========================

Base URL: https://api.notamify.com/api/v2
Authentication: Bearer token (set via NOTAMIFY_API_KEY environment variable)

Limitations:
- Maximum 5 ICAO codes per request
- Start date cannot be earlier than 1 day before current UTC time
- End date must be later than start date
- Page size limited to 1-30 items

Available endpoints:
- GET /notams - Retrieve NOTAMs with filtering options

Time format: ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
Example: 2024-01-01T00:00:00Z

Common ICAO codes:
- KJFK - John F. Kennedy International Airport (New York)
- EGLL - London Heathrow Airport
- EDDM - Munich Airport
- KLAX - Los Angeles International Airport
- KORD - Chicago O'Hare International Airport
- EDDF - Frankfurt Airport
"""


@mcp.prompt()
def analyze_notams(airport_codes: str) -> str:
    """
    Generate a prompt for analyzing NOTAMs at specified airports
    
    Args:
        airport_codes: Comma-separated ICAO airport codes
    
    Returns:
        Formatted prompt for NOTAM analysis
    """
    return f"""
Please analyze the current NOTAMs for the following airports: {airport_codes}

Use the get_notams tool to retrieve current NOTAM data and then provide:

1. Summary of active NOTAMs by category (navigation, runway, airspace, etc.)
2. Critical items that may affect flight operations
3. Temporary restrictions or warnings
4. Expected duration of significant NOTAMs
5. Recommendations for flight planning

Focus on operationally significant information that pilots and flight planners need to know.
"""


if __name__ == "__main__":
    # Run the server
    mcp.run() 