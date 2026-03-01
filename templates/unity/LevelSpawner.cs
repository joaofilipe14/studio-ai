using UnityEngine;
using System.Collections.Generic;

public static class LevelSpawner
{
    private static HashSet<Vector2Int> occupiedCells = new HashSet<Vector2Int>();
    public static List<Vector2Int> reachableCells = new List<Vector2Int>(); // NOVO: Guarda os caminhos válidos

    public static void ResetSpawns()
    {
        occupiedCells.Clear();
        reachableCells.Clear();
    }

    // ==========================================
    // ALGORITMO DE VALIDAÇÃO DE CAMINHO (BREADTH-FIRST SEARCH)
    // ==========================================
    public static void CalculateReachableArea(GridWorld world, Vector2Int startPos) {
        reachableCells.Clear();
        Queue<Vector2Int> queue = new Queue<Vector2Int>();
        HashSet<Vector2Int> visited = new HashSet<Vector2Int>();

        queue.Enqueue(startPos);
        visited.Add(startPos);

        Vector2Int[] dirs = { Vector2Int.up, Vector2Int.down, Vector2Int.left, Vector2Int.right };

        while (queue.Count > 0) {
            Vector2Int curr = queue.Dequeue();
            reachableCells.Add(curr);

            foreach (Vector2Int d in dirs) {
                Vector2Int next = curr + d;
                // Verifica se está dentro do mapa e se não é uma parede
                if (next.x >= 0 && next.x < world.Width && next.y >= 0 && next.y < world.Height) {
                    if (!world.IsBlocked(next) && !visited.Contains(next)) {
                        visited.Add(next);
                        queue.Enqueue(next);
                    }
                }
            }
        }
        Debug.Log($"[LevelSpawner] Mapeamento concluído. Células alcançáveis: {reachableCells.Count}");
    }

    public static Vector2Int GetUniqueSpawnPosition(GridWorld world, System.Random rng)
    {
        // Se já mapeámos o caminho, OBRIGA a nascer numa área acessível!
        if (reachableCells.Count > 10) {
            for (int i = 0; i < 100; i++) {
                Vector2Int pos = reachableCells[rng.Next(reachableCells.Count)];
                if (!occupiedCells.Contains(pos)) {
                    occupiedCells.Add(pos);
                    return pos;
                }
            }
        }

        // Fallback caso a área seja muito pequena ou ainda não tenha sido mapeada
        for (int i = 0; i < 100; i++) {
            Vector2Int pos = world.RandomFreeCell(rng);
            if (!occupiedCells.Contains(pos)) {
                occupiedCells.Add(pos);
                return pos;
            }
        }
        return world.RandomFreeCell(rng);
    }

    public static Vector2Int GetUniqueSpawnPositionFarFrom(GridWorld world, System.Random rng, Vector2Int targetPos, float minDistance)
    {
        // Força a nascer longe, MAS num sítio que tenha caminho até ti!
        if (reachableCells.Count > 10) {
            for (int i = 0; i < 200; i++) {
                Vector2Int pos = reachableCells[rng.Next(reachableCells.Count)];
                if (!occupiedCells.Contains(pos) && Vector2Int.Distance(pos, targetPos) >= minDistance) {
                    occupiedCells.Add(pos);
                    return pos;
                }
            }
        }

        for (int i = 0; i < 200; i++) {
            Vector2Int pos = world.RandomFreeCell(rng);
            if (!occupiedCells.Contains(pos) && Vector2Int.Distance(pos, targetPos) >= minDistance) {
                occupiedCells.Add(pos);
                return pos;
            }
        }
        return GetUniqueSpawnPosition(world, rng);
    }

    public static SimpleAgent SpawnAgent(GridWorld world, System.Random rng, float moveSpeed, bool isHuman, float visionRadius, string spriteName = "PlayerSprite")
    {
        Vector2Int start = GetUniqueSpawnPosition(world, rng);
        GameObject agentGO = new GameObject("Agent");

        Texture2D rawTex = Resources.Load<Texture2D>("Sprites/" + spriteName);
        if (rawTex == null) {
            Debug.LogWarning($"[LevelSpawner] Sprite '{spriteName}' não encontrado. A usar PlayerSprite padrão.");
            rawTex = Resources.Load<Texture2D>("Sprites/PlayerSprite");
        }

        Material baseMat = CreateSimpleMaterial(Color.white);
        VoxelRenderer.CreateVoxelSprite(agentGO.transform, rawTex, baseMat);

        SimpleAgent agent = agentGO.AddComponent<SimpleAgent>();
        agent.world = world;
        agent.gridPos = start;
        agent.moveSpeed = moveSpeed;
        agentGO.transform.position = world.GridToWorld(start);

        Camera mainCam = Camera.main;
        if (mainCam != null)
        {
            CameraController camController = mainCam.gameObject.GetComponent<CameraController>();
            if (camController == null) camController = mainCam.gameObject.AddComponent<CameraController>();
            camController.target = agentGO.transform;
            camController.isHumanMode = isHuman;
        }

        GameObject lightObj = new GameObject("PlayerLight");
        lightObj.transform.SetParent(agentGO.transform);
        lightObj.transform.localPosition = new Vector3(0, 0.5f, 0);
        Light playerLight = lightObj.AddComponent<Light>();
        playerLight.type = LightType.Point;
        playerLight.color = new Color(1f, 0.9f, 0.7f);
        playerLight.intensity = 5.0f;
        playerLight.shadows = LightShadows.Soft;
        playerLight.range = visionRadius > 0 ? visionRadius : 8.0f;

        return agent;
    }

    public static void SpawnEnemies(GridWorld world, System.Random rng, int count, float speed, Vector2Int playerPos, float minSafeDistance)
        {
            for (int i = 0; i < count; i++) {
                // Em vez de GetUniqueSpawnPosition, usamos a nossa função que respeita a distância!
                Vector2Int pos = GetUniqueSpawnPositionFarFrom(world, rng, playerPos, minSafeDistance);

                GameObject enemy = GameObject.CreatePrimitive(PrimitiveType.Cube);
                enemy.name = "Chaser_" + i;
                enemy.GetComponent<Renderer>().material = CreateSimpleMaterial(Color.red);

                ChaserAI ai = enemy.AddComponent<ChaserAI>();
                ai.world = world;
                ai.gridPos = pos;
                ai.moveSpeed = speed;
                enemy.transform.position = world.GridToWorld(pos);
            }
        }

    // ATUALIZADO: Agora pede a posição do jogador e a distância mínima
    public static void SpawnGoal(GridWorld world, System.Random rng, Vector2Int playerPos, float minDistance)
    {
        Vector2Int p = GetUniqueSpawnPositionFarFrom(world, rng, playerPos, minDistance);
        GameObject goal = GameObject.CreatePrimitive(PrimitiveType.Cube);
        goal.name = "Goal";
        goal.GetComponent<Renderer>().material = CreateSimpleMaterial(Color.cyan);
        goal.transform.position = world.GridToWorld(p, 0.5f);
        goal.AddComponent<Goal>().gridPos = p;
    }

    public static void SpawnCollectibles(GridWorld world, System.Random rng, int count)
    {
        for (int i = 0; i < count; i++) {
            Vector2Int p = GetUniqueSpawnPosition(world, rng);
            GameObject coin = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            coin.name = "Collectible";
            coin.tag = "Collectible";
            coin.transform.position = world.GridToWorld(p, 0.3f);
            coin.transform.localScale = Vector3.one * 0.5f;
            coin.GetComponent<Renderer>().material.color = Color.yellow;
            coin.AddComponent<Collectible>().gridPos = p;
        }
    }

    public static void SpawnPowerUps(GridWorld world, System.Random rng, int count)
    {
        for (int i = 0; i < count; i++) {
            Vector2Int p = GetUniqueSpawnPosition(world, rng);
            PowerUpType selectedType = (rng.Next(0, 2) == 0) ? PowerUpType.Time : PowerUpType.Speed;

            GameObject item = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            item.name = "PowerUp_" + selectedType;
            item.tag = "Collectible";

            Color col = (selectedType == PowerUpType.Time) ? Color.blue : Color.magenta;
            item.GetComponent<Renderer>().material = CreateSimpleMaterial(col);

            item.transform.position = world.GridToWorld(p, 0.5f);
            item.transform.localScale = new Vector3(0.5f, 0.1f, 0.5f);
            item.transform.rotation = Quaternion.Euler(90, 0, 0);

            PowerUp script = item.AddComponent<PowerUp>();
            script.type = selectedType;
            script.gridPos = p;

            item.GetComponent<Collider>().isTrigger = true;
            item.AddComponent<ItemAnimate>();
        }
    }

    public static void SpawnTraps(GridWorld world, System.Random rng, int count, float penalty)
    {
        for (int i = 0; i < count; i++) {
            Vector2Int p = GetUniqueSpawnPosition(world, rng);
            GameObject trapObj = GameObject.CreatePrimitive(PrimitiveType.Cube);
            trapObj.name = "Trap";
            trapObj.tag = "Collectible";

            trapObj.GetComponent<Renderer>().material = CreateSimpleMaterial(new Color(0.8f, 0.2f, 0.2f));
            trapObj.transform.position = world.GridToWorld(p, 0.05f);
            trapObj.transform.localScale = new Vector3(0.8f, 0.1f, 0.8f);

            Trap script = trapObj.AddComponent<Trap>();
            script.gridPos = p;
            script.penalty = penalty;
        }
    }

    private static Material CreateSimpleMaterial(Color color) {
        Shader safetyShader = Shader.Find("Unlit/Color");
        if (safetyShader == null) safetyShader = Shader.Find("Legacy Shaders/VertexLit");
        Material mat = new Material(safetyShader);
        mat.color = color;
        return mat;
    }
}