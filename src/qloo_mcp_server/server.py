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
import yaml
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
        if "entity_type" not in arguments:
            raise ValueError("Missing required argument 'entity' in arguments")
        if name == "get_insights":
            print(f"Calling get_insights with arguments: {arguments}")
            return get_insights_by_entity_type(entity_type = arguments["entity_type"], filters=arguments["filters"])
            # return get_insights(arguments["payload"])
        else:
            raise ValueError(f"Unknown tool: {name}")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        try:
            with open(os.path.join(os.path.dirname(__file__), "filter_desc.yaml"), "r", encoding="utf-8") as f:
                filter_desc = f.read()
                print("Filter description loaded successfully.", type(filter_desc))
            data = yaml.safe_load(filter_desc)
            filter_desc = yaml.dump(data, allow_unicode=True, sort_keys=False)
        except Exception as e:
            print(f"Error reading filter_desc.yaml: {e}", file=sys.stderr)
            filter_desc = "No description available due to error reading file."
        try:
            tools_to_send = [
                types.Tool(name= "get_insights",
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
        "properties": {

          "filter.address": {
            "type": "string",
            "description": "Filter by partial address (e.g., 'New York'). Applicable to: place"
          },
          "filter.content_rating": {
            "type": "string",
            "description": "Comma-separated list of MPAA content ratings (e.g., 'PG,PG-13'). Applicable to: movie, tv_show"
          },
          "filter.release_year.min": {
            "type": "integer",
            "description": "Minimum release year. Applicable to: movie, tv_show"
          },
          "filter.release_year.max": {
            "type": "integer",
            "description": "Maximum release year. Applicable to: movie, tv_show"
          },
          "filter.date_of_birth.min": {
            "type": "string",
            "description": "Minimum DOB in YYYY-MM-DD. Applicable to: person"
          },
          "filter.date_of_birth.max": {
            "type": "string",
            "description": "Maximum DOB in YYYY-MM-DD. Applicable to: person"
          },
          "filter.gender": {
            "type": "string",
            "description": "Gender identity filter (e.g., 'male', 'female'). Applicable to: person"
          },
          "filter.price_level.min": {
            "type": "integer",
            "description": "Minimum price level (1–4). Applicable to: place"
          },
          "filter.price_level.max": {
            "type": "integer",
            "description": "Maximum price level (1–4). Applicable to: place"
          },
          "filter.publication_year.min": {
            "type": "number",
            "description": "Minimum publication year. Applicable to: book"
          },
          "filter.publication_year.max": {
            "type": "number",
            "description": "Maximum publication year. Applicable to: book"
          },
          "filter.location": {
            "type": "string",
            "description": "WKT POINT or Qloo locality ID. Applicable to: place, destination"
          },
          "filter.location.radius": {
            "type": "integer",
            "description": "Radius in meters for fuzzy location match. Applicable to: place, destination"
          }
      }}
    }}                )

            ]
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