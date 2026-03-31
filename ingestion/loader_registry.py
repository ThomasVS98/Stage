from typing import Callable, Dict

LOADERS: Dict[str, Callable] = {}
SCHEMAS = {}

def register_loader(source_type: str, schema: dict = None):
    def wrapper(func: Callable):
        LOADERS[source_type] = func
        SCHEMAS[source_type] = schema or {}
        return func
    return wrapper

def get_loader(source_type: str) -> Callable:
    return LOADERS.get(source_type)

def get_available_loaders():
    return list(LOADERS.keys())

def get_schema(source_type: str):
    return SCHEMAS.get(source_type, {})