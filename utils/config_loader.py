import json
import os
import uuid
from utils.logging import get_logger
from config.settings import settings
from typing import Any

logger = get_logger(__name__)

CONFIG_PATH = os.path.join("config", "sources.json")


def resolve_env(config: dict[str, Any]) -> dict[str, Any]:
    """
    Vervangt configuratiewaarden die verwijzen naar environment variabelen.

    Strings die eindigen op "_ID" worden geïnterpreteerd als verwijzing
    naar een waarde in settings.

    Args:
        config (dict[str, Any]): Ruwe configuratie.

    Returns:
        dict[str, Any]: Configuratie met opgeloste environment waarden.
    """
    resolved: dict[str, Any] = {}

    for key, value in config.items():
        if isinstance(value, str) and value.endswith("_ID"):
            env_val = getattr(settings, value, None)
            if env_val is None:
                logger.warning("ENV var niet gevonden: %s", value)
                resolved[key] = value
            else:
                resolved[key] = env_val
        else:
            resolved[key] = value

    return resolved


def load_source_config(resolve: bool = True) -> list[dict[str, Any]]:
    """
    Laadt bronconfiguratie uit het JSON bestand.

    - voegt ontbrekende IDs toe
    - lost environment variabelen op indien gevraagd

    Args:
        resolve (bool): Indien True, worden environment variabelen opgelost.

    Returns:
        list[dict[str, Any]]: Lijst van bronconfiguraties.
    """
    try:
        with open(CONFIG_PATH, "r") as f:
            raw = json.load(f)
    except Exception as e:
        logger.exception("Config laden mislukt: %s", e)
        return []

    resolved = []
    updated_raw = []
    changed = False

    for source in raw:
        source_entry = source.copy()
        if "id" not in source_entry:
            new_id = str(uuid.uuid4())
            source_entry["id"] = new_id
            changed = True

        updated_raw.append(source_entry)

        if resolve:
            resolved_source = source_entry.copy()
            resolved_source["config"] = resolve_env(
                source_entry.get("config", {})
            ).copy()
            resolved.append(resolved_source)

    if changed:
        save_source_config(updated_raw)

    return resolved if resolve else updated_raw


def save_source_config(sources: list[dict[str, Any]]) -> None:
    """
    Slaat bronconfiguratie op naar het JSON bestand.

    Args:
        sources (list[dict[str, Any]]): Configuraties om op te slaan.
    """
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(sources, f, indent=2)
        logger.info("Config succesvol opgeslagen")
    except Exception as e:
        logger.exception("Config opslaan mislukt: %s", e)
