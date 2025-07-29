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

from src.qloo_mcp_server.get_insights import get_insights
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
    async def qloo_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if "payload" not in arguments:
            raise ValueError("Missing required argument 'payload'")
        if name == "get_insights":
            return get_insights(arguments["payload"])
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
                types.Tool(
                    name = "get_insights",
                    description = "get the insights for a given entity and filter. entity can be only one from the list ['artist','brand','movie', 'tv_show', 'book', 'place', 'podcast','video_game', 'music','destination','person'] and there is different filters for each entity type. Configure the filters in the payload.",
                    inputSchema = {
                    "type": "object",
                    "required": [
                        "payload"
                    ],
                    "properties": {
                        "payload": {
                            "type": "object",
                            "description": "Payload is a JSON object that contains the entity type and filters. The entity type must be one of the following: ['artist','brand','movie', 'tv_show', 'book', 'place', 'podcast','video_game', 'music','destination','person']. The filters are specific to each entity type and can include parameters like price level, publication year, release date, etc. Refer to the documentation for the specific filters available for each entity type. Entity always should be with filter.type key and value for this key is always urn:entity:<entity>. All the filter with their description are as {filter_desc_add}. Make sure payload must have filter.type with atleast one filters from filters list. Sample payload for a movie entity might look like: {{\"filter.type\": \"urn:entity:movie\", \"filter.address\": \"New York\", \"filter.release_year.min\": 2000, \"filter.release_year.max\": 2020}}.".format(filter_desc_add=str(filter_desc)),
                        }
                    },
                }
                )
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