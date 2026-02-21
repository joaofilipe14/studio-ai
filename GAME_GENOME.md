# GAME_GENOME.md

## O que é o “Game Genome”?
É um ficheiro de configuração (JSON) que descreve **o jogo/nível** de forma parametrizada.
Em vez de “hardcode” no BuildScript, o BuildScript lê o genome e gera:
- tamanho da arena
- número/tipo de obstáculos
- regras do goal
- timer
- parâmetros do agente
- modo de jogo (maze/arena/collect/etc.)

**Serve para:**
1) reproducibilidade (seed + genome = mesmo nível),
2) evolução automática (mutar números e regras),
3) controlo de dificuldade (director ajusta parâmetros),
4) comparar jogos (métricas por genome).

---

## Conceitos
- **seed**: controla aleatoriedade; com o mesmo seed, o nível é igual.
- **episode/round**: uma tentativa do agente.
- **difficulty target**: queremos win_rate numa faixa (ex: 60%).

---

## Exemplo de genome.json

```json
{
  "version": "1.1",
  "seed": 42,
  "description": "Arena de teste com navegação NavMesh",
  "arena": {
    "halfSize": 8.0,
    "walls": true,
    "floorMaterial": "Grid_Default"
  },
  "agent": {
    "type": "NavMesh",
    "speed": 5.0,
    "acceleration": 15.0,
    "angularSpeed": 720.0,
    "stopDistance": 0.5,
    "stuckTimeout": 2.5
  },
  "obstacles": {
    "count": 8,
    "minSize": [1.0, 1.0, 1.0],
    "maxSize": [2.5, 3.0, 2.5],
    "mode": "random_arena",
    "ensurePath": true
  },
  "rules": {
    "timeLimit": 20.0,
    "rounds": 5,
    "difficultyMultiplier": 1.0,
    "winCondition": "reach_goal"
  }
}