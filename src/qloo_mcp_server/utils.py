from typing import Dict, Any
from urllib.parse import quote

def encode_form_query(data: Dict[str, Any], explode: bool = False) -> str:
    def encode_value(value):
        if isinstance(value, list):
            return ",".join(quote(str(v), safe="")) if not explode else [
                (key, quote(str(v), safe="")) for v in value
            ]
        elif value is None:
            return None
        return quote(str(value), safe="")

    query_params = []
    for key, value in data.items():
        if value is None:
            continue
        encoded_key = quote(key, safe="")

        if isinstance(value, list):
            if explode:
                for v in value:
                    query_params.append(f"{encoded_key}={quote(str(v), safe='')}")
            else:
                joined = ",".join(quote(str(v), safe="") for v in value)
                query_params.append(f"{encoded_key}={joined}")
        else:
            encoded_value = quote(str(value), safe="")
            query_params.append(f"{encoded_key}={encoded_value}")

    return "&".join(query_params)