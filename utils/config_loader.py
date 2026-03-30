import json
import os
from utils.logging import get_logger

logger = get_logger(__name__)

CONFIG_PATH = os.path.join("config", "sources.json")

def load_source_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            raw = json.load(f)
    except Exception as e:
        logger.exception("Config laden mislukt: %s", e)
        return []
    
    resolved = []

    for source in raw:
        new_source = source.copy()
        config = new_source.get("config", {}).copy()
        for key, value in config.items():
            if isinstance(value, str) and value.endswith("_ID"):
                env_val = os.getenv(value)
                if not env_val:
                    logger.warning("ENV var niet gevonden: %s", value)
                config[key] = env_val
        new_source["config"] = config
        resolved.append(new_source)
    return resolved

def save_source_config(sources: list):
    try:
        with open(CONFIG_PATH, "w") as f:
                json.dump(sources, f, indent=2)
        logger.info("Config succesvol opgeslagen")
    except Exception as e:
        logger.exception("Config opslaan mislukt: %s", e)