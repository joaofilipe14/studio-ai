from fastapi import APIRouter
from shared.models import GameEvolutionRequest
from services.game_director.logic import evolve_bot_genome, evolve_human_genome

router = APIRouter(prefix="/director", tags=["Director"])

@router.post("/evolve")
async def evolve(request: GameEvolutionRequest):
    genome_dict = request.current_genome.dict()
    if request.is_human:
        return evolve_human_genome(request.config, request.metrics, genome_dict)
    return evolve_bot_genome(request.config, request.metrics, genome_dict)