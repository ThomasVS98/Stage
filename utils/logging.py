import logging
import os


def setup_logging() -> None:
    """
    Initialiseert de globale logging configuratie.

    Leest het log level uit de environment variabele LOG_LEVEL
    (default: INFO) en configureert het standaard logformaat.
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    """
    Haalt een logger instantie op met een gegeven naam.

    Args:
        name (str): Naam van de logger (meestal __name__).

    Returns:
        logging.Logger: Logger instantie.
    """
    return logging.getLogger(name)
