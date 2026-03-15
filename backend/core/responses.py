def ok(data=None, message: str = "success"):
    return {"code": 200, "message": message, "data": data}


def fail(message: str, code: int = 500):
    return {"code": code, "message": message, "data": None}


def to_float(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default
