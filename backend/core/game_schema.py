from pydantic import BaseModel
from typing import List, Dict

class SwipeSortGame(BaseModel):
    game_type: str
    left_category: str
    right_category: str
    cards: List[str]
    answer_key: Dict[str, str]
    why: Dict[str, str]

class ImpostorGame(BaseModel):
    game_type: str
    options: List[str]
    impostor: str
    why: str

class MatchPairsGame(BaseModel):
    game_type: str
    pairs: Dict[str, str]
    why: Dict[str, str]

class GameBatch(BaseModel):
    """Batch of 5 games of the same type"""
    concept: str
    game_type: str
    games: List[Dict]  # List of 5 game objects
    batch_number: int  # Track which batch this is (1, 2, 3...)
