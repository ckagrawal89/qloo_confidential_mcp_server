
import httpx
from typing import Dict, Any
from urllib.parse import quote
from src.qloo_mcp_server.constant import QLOO_API, QLOO_API_KEY
from src.qloo_mcp_server.utils import encode_form_query




def clean_audience_response(response: httpx.Response) -> Dict[str, Any]:
    

    try:
        res_data = response.json()
        audiences = res_data.get("results", {})
        if "audiences" in audiences:
            audiences = audiences.get("audiences", [])
            keys_to_remove = ["entity_id","parents","type","id","disambiguation","tags"]
        elif "audience_types" in audiences:
            audiences = audiences.get("audience_types", [])
            keys_to_remove =["parents"]
        for audience in audiences:

            for key in keys_to_remove:
                audience.pop(key, None)

        return res_data
    except (httpx.JSONDecodeError, ValueError):
        return {"ok": False, "error": "Invalid JSON response"}

def get_audience_types() -> Dict[str, Any]:
    if not QLOO_API_KEY:
        return {"ok": False, "error": "QLOO_API_KEY is required for API calls"}

    url = f"{QLOO_API.rstrip('/')}/v2/audiences/types"
    headers = {
        "Accept": "application/json",
        "X-API-Key": QLOO_API_KEY
    }
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=headers)
        clean_data = clean_audience_response(response)
        if response.status_code == 200:
            return {"ok": True, "data": clean_data}
        return {"ok": False, "status_code": response.status_code, "error": response.text}
    except httpx.RequestError as e:
        return {"ok": False, "error": f"Network error: {e}"}


def get_audience_by_type(parent_type: str) -> Dict[str, Any]:
    if not QLOO_API_KEY:
        return {"ok": False, "error": "QLOO_API_KEY is required for API calls"}
    if not parent_type or not str(parent_type).startswith("urn:audience:"):
        return {"ok": False, "error": "parent type must start with 'urn:audience:'"}

    payload = {"filter.parents.types": parent_type}
    

    query_string = encode_form_query(payload, explode=False)
    url = f"{QLOO_API.rstrip('/')}/v2/audiences"
    headers = {
        "Accept": "application/json",
        "X-API-Key": QLOO_API_KEY
    }
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, params=query_string, headers=headers)
        clean_data = clean_audience_response(response)
        if response.status_code == 200:
            return {"ok": True, "data": clean_data}
        return {"ok": False, "status_code": response.status_code, "error": response.text}
    except httpx.RequestError as e:
        return {"ok": False, "error": f"Network error: {e}"}