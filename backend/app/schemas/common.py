from typing import Any


def envelope(data: Any) -> dict:
    return {"success": True, "data": data}
