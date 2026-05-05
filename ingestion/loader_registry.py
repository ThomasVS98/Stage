from typing import Callable, Dict

LOADERS: Dict[str, Callable] = {}
SCHEMAS: Dict[str, dict] = {}


def register_loader(source_type: str, schema: dict | None = None) -> Callable:
    """
    Registreert een loader functie voor een bepaald brontype.

    Wordt gebruikt als decorator om loaders dynamisch toe te voegen
    aan de loader registry.

    Args:
        source_type (str): Type van de bron (bv. 'sharepoint', 'topdesk').
        schema (dict | None): Optioneel schema voor configuratievalidatie.

    Returns:
        Callable: Wrapper functie die de loader registreert.
    """

    def wrapper(func: Callable) -> Callable:
        LOADERS[source_type] = func
        SCHEMAS[source_type] = schema or {}
        return func

    return wrapper


def get_loader(source_type: str) -> Callable | None:
    """
    Haalt de loader functie op voor een gegeven brontype.

    Args:
        source_type (str): Type van de bron.

    Returns:
        Callable | None: Loader functie of None indien niet gevonden.
    """
    return LOADERS.get(source_type)


def get_available_loaders() -> list[str]:
    """
    Geeft een lijst van alle beschikbare loader types.

    Returns:
        list[str]: Lijst van geregistreerde loader types.
    """
    return list(LOADERS.keys())


def get_schema(source_type: str) -> dict:
    """
    Haalt het configuratieschema op voor een gegeven brontype.

    Args:
        source_type (str): Type van de bron.

    Returns:
        dict: Schema voor configuratie (leeg dict indien niet gevonden).
    """
    return SCHEMAS.get(source_type, {})
