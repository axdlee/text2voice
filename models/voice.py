from dataclasses import dataclass
from typing import Optional

@dataclass
class Voice:
    """音色模型"""
    id: str
    name: str
    model: str
    is_custom: bool = False
    description: Optional[str] = None 