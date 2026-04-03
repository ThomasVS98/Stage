import json
import os
import uuid
from utils.logging import get_logger
from config.settings import settings

logger = get_logger(__name__)

CONFIG_PATH = os.path.join("config", "sources.json")

def resolve_env(config: dict) -> dict:
    resolved = {}

    for key, value in config.items():
            if isinstance(value, str) and value.endswith("_ID"):
                env_val = getattr(settings, value, None)
                if not env_val:
                    logger.warning("ENV var niet gevonden: %s", value)
                    resolved[key] = value
                else:
                    resolved[key] = env_val
            else:
                resolved[key] = value

    return resolved

def load_source_config():
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
        raw_source = source.copy()
        resolved_source = source.copy()
        if "id" not in raw_source:
            new_id = str(uuid.uuid4())
            raw_source["id"] = new_id
            resolved_source["id"] = new_id
            changed = True

        config = raw_source.get("config", {}).copy()
        resolved_config = resolve_env(config)

        resolved_source["config"] = resolved_config

        updated_raw.append(raw_source)
        resolved.append(resolved_source)

    if changed:
        save_source_config(updated_raw)

    return resolved

def save_source_config(sources: list):
    try:
        with open(CONFIG_PATH, "w") as f:
                json.dump(sources, f, indent=2)
        logger.info("Config succesvol opgeslagen")
    except Exception as e:
        logger.exception("Config opslaan mislukt: %s", e)