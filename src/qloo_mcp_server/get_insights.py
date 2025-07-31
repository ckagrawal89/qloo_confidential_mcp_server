import time
import httpx
from typing import Optional, Dict, Any
from urllib.parse import quote
from src.qloo_mcp_server.constant import QLOO_API, QLOO_API_KEY
import json
from src.qloo_mcp_server.utils import encode_form_query


def clean_response(response: httpx.Response) -> Dict[str, Any]:
    keys_to_remove = [
        "entity_id", "type", "subtype", "popularity", "tags", "query",
        "disambiguation", "external"
    ]
    properties_keys_to_remove = [
        "format", "isbn10", "isbn13", "publication_year", "short_description",
        "short_descriptions", "release_year", "content_rating", "akas",
        "keywords"
    ]

    try:
        res_data = response.json()
        entities = res_data.get("results", {}).get("entities", [])
        for entity in entities:

            for key in keys_to_remove:
                entity.pop(key, None)
            
            props = entity.get("properties", {})
            if isinstance(props, dict):
                for prop_key in properties_keys_to_remove:
                    props.pop(prop_key, None)
        return res_data
    except (httpx.JSONDecodeError, ValueError):
        return {"ok": False, "error": "Invalid JSON response"}


def get_insights(payload) -> Dict[str, Any]:
    if not payload:
        return {"ok": False, "error": "Payload cannot be empty"}
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return {"ok": False, "error": "Invalid JSON payload"}
    elif not isinstance(payload, dict):
        return {"ok": False, "error": "Payload must be a JSON object or string"}
    if not QLOO_API_KEY:
        return {"ok": False, "error": "QLOO_API_KEY is required for API calls"}
    if "filter.type" not in payload or not str(payload.get("filter.type", "")).startswith("urn:entity:"):
        return {"ok": False, "error": "Payload must contain 'filter.type' starting with 'urn:entity:'"}

    payload.setdefault("take", 10)
    query_string = encode_form_query(payload, explode=False)
    url = f"{QLOO_API.rstrip('/')}/v2/insights"
    headers = {
        "Accept": "application/json",
        "X-API-Key": QLOO_API_KEY
    }
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, params=query_string, headers=headers)
        clean_data = clean_response(response)
        if response.status_code == 200:
            return {"ok": True, "data": clean_data}
        return {"ok": False, "status_code": response.status_code, "error": response.text}
    except httpx.RequestError as e:
        return {"ok": False, "error": f"Network error: {e}"}
    

def get_insights_by_entity_type(entity_type: str, filters: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"filter.type": entity_type}
    if filters:
        payload.update(filters)
    return get_insights(payload)
