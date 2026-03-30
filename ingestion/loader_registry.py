from typing import Callable, Dict

LOADERS: Dict[str, Callable] = {}

def register_loader(source_type: str):
    def wrapper(func: Callable):
        LOADERS[source_type] = func
        return func
    return wrapper

def get_loader(source_type: str) -> Callable:
    return LOADERS.get(source_type)

def get_available_loaders():
    return list(LOADERS.keys())