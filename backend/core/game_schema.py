from pydantic import BaseModel
from typing import List, Dict

class SwipeSortGame(BaseModel):
    game_type: str
    left_category: str
    right_category: str
    cards: List[str]

class ImpostorGame(BaseModel):
    game_type: str
    options: List[str]
    impostor: str

class MatchPairsGame(BaseModel):
    game_type: str
    pairs: Dict[str, str]
