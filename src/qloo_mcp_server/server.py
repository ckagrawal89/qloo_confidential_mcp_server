import contextlib
from collections.abc import AsyncIterator
import os, io
import click
import httpx
import uvicorn
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import PlainTextResponse
from starlette.types import Receive, Scope, Send

from src.qloo_mcp_server.get_insights import get_insights_by_entity_type
from gramine_ratls.attest import write_ra_tls_key_and_crt
import sys



@click.command()
@click.option("--port", default=8000, help="Port to listen on for StreamableHTTP")
@click.option(
    "--isDev",
    "isDev",
    is_flag=True,
    help="Is development mode on",
)

# Add an option for API key

def main(port: int, isDev: bool) -> int:
    
    if not isDev:
        key_file_path = "/app/tmp/key.pem"
        crt_file_path = "/app/tmp/crt.pem"
        write_ra_tls_key_and_crt(key_file_path, crt_file_path, format="pem")
    # Store API key for use in API calls


    app = Server("qloo-mcp-server")

    @app.call_tool()
    async def qloo_tool(name: str, arguments: dict):
        
        if name == "get_insights":
            return get_insights_by_entity_type(entity_type = arguments["entity_type"], filters=arguments["filters"])
            # return get_insights(arguments["payload"])
        elif name == "get_audience_types":
            from src.qloo_mcp_server.get_audience import get_audience_types
            return get_audience_types()
        elif name == "get_audience_by_type":
            from src.qloo_mcp_server.get_audience import get_audience_by_type
            return get_audience_by_type(parent_type=arguments["parent_type"])
        else:
            raise ValueError(f"Unknown tool: {name}")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        try:
            tools_to_send = [
                types.Tool(
                    name= "get_insights",
                    description=  "Fetch insights for a specific entity type by applying relevant filters. Must include 'filter.type' (e.g., 'urn:entity:movie') and at least one other valid filter. Entity can be only one from the list ['artist','brand','movie', 'tv_show', 'book', 'place', 'podcast','video_game', 'music','destination','person'] and there is different filters for each entity type. Configure the filters in the payload.",
                    inputSchema= {
                        "type": "object",
                        "properties": {
                          "entity_type": {
                              "type": "string",
                              "description": "URN identifier for the entity type. Must be one of: 'urn:entity:artist', 'urn:entity:brand', 'urn:entity:movie', 'urn:entity:tv_show', 'urn:entity:book', 'urn:entity:place', 'urn:entity:podcast', 'urn:entity:video_game', 'urn:entity:music', 'urn:entity:destination', 'urn:entity:person'."
                          },
                          "filters": {
                            "type": "object",
                            "description": "A JSON object containing the applicable filters based on the entity. At least one filter must be present.",
                            "properties" : {
                              "filter.address": {
                                  "type": "string",
                                  "description": "Find places by matching part of their address, like a city or street name. Available to: Place"
                              },
                              "filter.content_rating": {
                                  "type": "string",
                                  "description": "Filter movies or TV shows by MPAA ratings, like 'PG' or 'PG-13'. Available to: Movie, TV Show"
                              },
                              "filter.release_year.min": {
                                  "type": "integer",
                                  "description": "Only include movies or TV shows released after this year. Available to: Movie, TV Show"
                              },
                              "filter.release_year.max": {
                                  "type": "integer",
                                  "description": "Only include movies or TV shows released before this year. Available to: Movie, TV Show"
                              },
                              "filter.date_of_birth.min": {
                                  "type": "string",
                                  "description": "Only include people born after this date (YYYY-MM-DD). Available to: Person"
                              },
                              "filter.date_of_birth.max": {
                                  "type": "string",
                                  "description": "Only include people born before this date (YYYY-MM-DD). Available to: Person"
                              },
                              "filter.gender": {
                                  "type": "string",
                                  "description": "Filter people by gender, like 'male' or 'female'. Available to: Person"
                              },
                              "filter.price_level.min": {
                                  "type": "integer",
                                  "description": "Only include places with a price level at least this value (1-4). Available to: Place"
                              },
                              "filter.price_level.max": {
                                  "type": "integer",
                                  "description": "Only include places with a price level at most this value (1-4). Available to: Place"
                              },
                              "filter.publication_year.min": {
                                  "type": "number",
                                  "description": "Only include books published after this year. Available to: Book"
                              },
                              "filter.publication_year.max": {
                                  "type": "number",
                                  "description": "Only include books published before this year. Available to: Book"
                              },
                              "filter.location": {
                                  "type": "string",
                                  "description": "Find places or destinations by location, using a WKT POINT or locality ID. Available to: Place, Destination"
                              },
                              "filter.location.radius": {
                                  "type": "integer",
                                  "description": "Set the search radius in meters around the location. Available to: Place, Destination"
                              },
                              "filter.audience.types": {
                                  "type": "string",
                                  "description": "Filter by a list of audience types."
                              },
                              "filter.external.resy.count.max": {
                                  "type": "integer",
                                  "description": "Only include places with a Resy rating count at most this value. Available to: Place"
                              },
                              "filter.external.resy.count.min": {
                                  "type": "integer",
                                  "description": "Only include places with a Resy rating count at least this value. Available to: Place"
                              },
                              "filter.external.resy.party_size.max": {
                                  "type": "integer",
                                  "description": "Only include places with a Resy party size at most this value. Available to: Place"
                              },
                              "filter.external.resy.party_size.min": {
                                  "type": "integer",
                                  "description": "Only include places with a Resy party size at least this value. Available to: Place"
                              },
                              "filter.external.resy.rating.max": {
                                  "type": "number",
                                  "description": "Only include places with a Resy rating at most this value. Available to: Place"
                              },
                              "filter.external.resy.rating.min": {
                                  "type": "number",
                                  "description": "Only include places with a Resy rating at least this value. Available to: Place"
                              },
                              "filter.finale_year.max": {
                                  "type": "integer",
                                  "description": "Only include TV shows with a final season before this year. Available to: TV Show"
                              },
                              "filter.finale_year.min": {
                                  "type": "integer",
                                  "description": "Only include TV shows with a final season after this year. Available to: TV Show"
                              },
                              "filter.exclude.location": {
                                  "type": "string",
                                  "description": "Exclude results inside a specific location, using WKT or locality ID. Available to: Destination, Place"
                              },
                              "filter.location.query": {
                                  "type": "string",
                                  "description": "Search for localities by name or ID. Available to: Destination, Place"
                              },
                              "filter.exclude.location.query": {
                                  "type": "string",
                                  "description": "Exclude results inside a specific locality, using name or ID. Available to: Destination, Place"
                              },
                              "filter.location.geohash": {
                                  "type": "string",
                                  "description": "Filter by geohash prefix to find places in a region. Available to: Destination, Place"
                              },
                              "filter.exclude.location.geohash": {
                                  "type": "string",
                                  "description": "Exclude places whose geohash starts with this prefix. Available to: Destination, Place"
                              },
                              "filter.price_range.from": {
                                  "type": "integer",
                                  "description": "Only include places with a minimum price at least this value. Available to: Place"
                              },
                              "filter.price_range.to": {
                                  "type": "integer",
                                  "description": "Only include places with a maximum price at most this value. Available to: Place"
                              },
                              "filter.release_country": {
                                  "type": "string",
                                  "description": "Filter by countries where a movie or TV show was released. Available to: Movie, TV Show"
                              },
                              "filter.release_date.max": {
                                  "type": "string",
                                  "description": "Only include items released before this date (YYYY-MM-DD)."
                              },
                              "filter.release_date.min": {
                                  "type": "string",
                                  "description": "Only include items released after this date (YYYY-MM-DD)."
                              }
                            }
                          }
                        }
                    }
                  ),
                  types.Tool(
                    name="get_audience_types",
                    description="Fetch all audience types available in the QLOO API. when you call this tool, it will return a list of all audience types. remove the urn:audience: prefix from the audience type.",
                    inputSchema={
                        "type": "object",
                        "properties": {None: {"type": "null"}},
                    }
                  ),
                  types.Tool(
                    name="get_audience_by_type",
                    description="Fetch audiences by a specific parent type. The parent type must start with 'urn:audience:'.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "parent_type": {
                                "type": "string",
                                "description": "Parent type to filter audiences by, must start with 'urn:audience:'. Audiences must be one of the following: 'urn:audience:artist', 'urn:audience:brand', 'urn:audience:movie', 'urn:audience:tv_show', 'urn:audience:book', 'urn:audience:place', 'urn:audience:podcast', 'urn:audience:video_game', 'urn:audience:music', 'urn:audience:destination', 'urn:audience:person'.'urn:audience:communities','urn:audience:global_issues','urn:audience:hobbies_and_interests','urn:audience:investing_interests','urn:audience:leisure','urn:audience:life_stage','urn:audience:lifestyle_preferences_beliefs','urn:audience:political_preferences','urn:audience:professional_area','urn:audience:spending_habits'"
                            }
                        }
                    }
                  )]
        except Exception as e:
            print(f"Error creating tools: {e}", file=sys.stderr)
            tools_to_send = []
        return tools_to_send

    # Create the session manager with true stateless mode
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=True,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            print("Application started with StreamableHTTP session manager!")
            try:
                yield
            finally:
                print("Application shutting down...")

    # Create an ASGI application using the transport
    starlette_app = Starlette(
        debug=True,
        routes=[
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )


    if isDev:
        uvicorn.run(starlette_app, host="0.0.0.0", port=port, workers=1, reload=False)
    else:
        uvicorn.run(starlette_app, host="0.0.0.0", port=port, workers=1, reload=False, ssl_keyfile=key_file_path, ssl_certfile=crt_file_path)

if __name__ == "__main__":
    main()