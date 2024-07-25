import json
from hashlib import md5
from neo4j.spatial import Point


def chunks(lst, n=1000):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def clean_float(value: float):
    as_int = int(value)
    if value == as_int:
        value = as_int
    return value


def serialize(obj):
    json_args = {'separators': (',', ':'), 'ensure_ascii': False}

    if isinstance(obj, list):
        return json.dumps([serialize(d) for d in obj], **json_args)
    elif isinstance(obj, dict) and obj is not None:
        return ''.join([f'{k}:{serialize(v)}' for k, v in sorted(obj.items(), key=lambda d: d[0])])
    elif isinstance(obj, float):
        return str(clean_float(obj))
    elif isinstance(obj, Point):
        return json.dumps(obj, **json_args)
    elif isinstance(obj, bool):
        return json.dumps(obj, **json_args)
    return obj


def checksum(obj):
    return md5(serialize(obj).encode()).hexdigest()
