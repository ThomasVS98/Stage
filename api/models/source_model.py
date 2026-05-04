from pydantic import BaseModel
from typing import Dict, Any


class SourceModel(BaseModel):
    """
    Model dat een configureerbare kennisbron voor ingestie voorstelt.

    Wordt gebruikt in de admin interface en API om bronnen te definiëren en beheren.

    Attributes:
        id (str | None): Unieke identifier voor de bron. Wordt automatisch gegenereerd bij creatie.
        type (str): Type van de bron (bepaalt welke loader gebruikt wordt).
        enabled (bool): Of de bron actief is voor ingestie. Standaard True.
        config (Dict[str, Any]): Configuratieparameters specifiek voor het type bron.
    """

    id: str | None = None
    type: str
    enabled: bool = True
    config: Dict[str, Any]
