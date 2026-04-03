from pydantic import BaseModel
from typing import Dict, Any

class SourceModel(BaseModel):
    id: str | None = None
    type: str
    enabled: bool = True
    config: Dict[str, Any]