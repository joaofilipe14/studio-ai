from pydantic import BaseModel
from typing import List, Optional

# --- LEVEL GENOME ---
class ArenaConfig(BaseModel):
    halfSize: float
    walls: bool

class ObstacleConfig(BaseModel):
    count: int
    minScale: float
    maxScale: float

class RulesConfig(BaseModel):
    timeLimit: float
    targetCount: int
    enemyCount: int
    enemySpeed: float
    powerUpCount: int
    powerUpType: Optional[str] = "Mixed"
    trapCount: int
    trapPenalty: Optional[float] = 2.0

class LevelGenomeModel(BaseModel):
    level_id: int
    mode: str
    seed: int
    theme: str
    arena: ArenaConfig
    obstacles: ObstacleConfig
    rules: RulesConfig

# --- ROSTER & PLAYER ---
class CharacterStats(BaseModel):
    speed: float
    acceleration: float
    visionRadius: float
    trapResistance: float

class CharacterClass(BaseModel):
    id: str
    name: str
    description: str
    spriteName: str
    cost: int
    stats: CharacterStats

class PlayerSaveModel(BaseModel):
    playerName: str
    currentCampaignLevel: int
    wallet: dict
    loadout: dict
    unlockedClasses: List[str]
    purchasedUpgrades: dict
    stats: dict

# --- REQUESTS ---
class GameEvolutionRequest(BaseModel):
    config: dict
    metrics: dict
    current_genome: LevelGenomeModel
    is_human: bool = False