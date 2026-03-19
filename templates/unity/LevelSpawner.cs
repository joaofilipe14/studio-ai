using UnityEngine;
using System.Collections.Generic;

public static class LevelSpawner
{
    private static HashSet<Vector2Int> occupiedCells = new HashSet<Vector2Int>();
    public static List<Vector2Int> reachableCells = new List<Vector2Int>();

    public static void ResetSpawns()
    {
        occupiedCells.Clear();
        reachableCells.Clear();
    }

    // ==========================================
    // CARREGADOR DE TEXTURAS UNIVERSAL
    // ==========================================
    private static Material CreateTexturedMaterial(string textureName, Color fallbackColor) {
        Texture2D tex = Resources.Load<Texture2D>("Textures/" + textureName);

        Shader standardShader = Shader.Find("Standard");
        if (standardShader == null) standardShader = Shader.Find("Legacy Shaders/VertexLit");
        Material mat = new Material(standardShader);

        if (tex != null) {
            mat.color = Color.white; // 🚨 Respeita a arte gerada pela IA!
            mat.mainTexture = tex;
        } else {
            mat.color = fallbackColor;
        }

        mat.SetFloat("_Glossiness", 0.6f);
        // Também removemos a Emissão daqui. As luzes de ponto coladas às moedas já fazem o brilho!
        return mat;
    }

    public static Material CreateSimpleMaterial(Color color) {
        Shader standardShader = Shader.Find("Standard");
        if (standardShader == null) standardShader = Shader.Find("Legacy Shaders/VertexLit");
        Material mat = new Material(standardShader);
        mat.color = color;
        return mat;
    }

    // ==========================================
    // ALGORITMO DE VALIDAÇÃO DE CAMINHO (BFS)
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
                if (next.x >= 0 && next.x < world.Width && next.y >= 0 && next.y < world.Height) {
                    if (!world.IsBlocked(next) && !visited.Contains(next)) {
                        visited.Add(next);
                        queue.Enqueue(next);
                    }
                }
            }
        }
    }

    public static Vector2Int GetUniqueSpawnPosition(GridWorld world, System.Random rng)
    {
        if (reachableCells.Count > 10) {
            for (int i = 0; i < 100; i++) {
                Vector2Int pos = reachableCells[rng.Next(reachableCells.Count)];
                if (!occupiedCells.Contains(pos)) {
                    occupiedCells.Add(pos);
                    return pos;
                }
            }
        }

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

    // ==========================================
    // SPAWNERS
    // ==========================================
    public static SimpleAgent SpawnAgent(GridWorld world, System.Random rng, float moveSpeed, bool isHuman, float visionRadius, string spriteName = "PlayerSprite")
    {
        Vector2Int start = GetUniqueSpawnPosition(world, rng);
        GameObject agentGO = new GameObject("Agent");

        Texture2D rawTex = Resources.Load<Texture2D>("Sprites/" + spriteName);
        if (rawTex == null) rawTex = Resources.Load<Texture2D>("Sprites/PlayerSprite");

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
            Vector2Int pos = GetUniqueSpawnPositionFarFrom(world, rng, playerPos, minSafeDistance);

            // INIMIGOS EM VOXELS (3D)!
            GameObject enemy = new GameObject("Chaser_" + i);

            Texture2D rawTex = Resources.Load<Texture2D>("Sprites/EnemySprite");
            if (rawTex == null) rawTex = Resources.Load<Texture2D>("Sprites/PlayerSprite");

            Material baseMat = CreateSimpleMaterial(Color.white);
            VoxelRenderer.CreateVoxelSprite(enemy.transform, rawTex, baseMat);

            // Adiciona uma luz vermelha assustadora ao inimigo para o veres aproximar no escuro!
            GameObject lightObj = new GameObject("EnemyLight");
            lightObj.transform.SetParent(enemy.transform);
            lightObj.transform.localPosition = new Vector3(0, 0.5f, 0);
            Light enemyLight = lightObj.AddComponent<Light>();
            enemyLight.type = LightType.Point;
            enemyLight.color = Color.red;
            enemyLight.intensity = 3.0f;
            enemyLight.range = 6.0f;

            ChaserAI ai = enemy.AddComponent<ChaserAI>();
            ai.world = world;
            ai.gridPos = pos;
            ai.moveSpeed = speed;
            enemy.transform.position = world.GridToWorld(pos);
        }
    }

    public static void SpawnGoal(GridWorld world, System.Random rng, Vector2Int playerPos, float minDistance)
    {
        Vector2Int p = GetUniqueSpawnPositionFarFrom(world, rng, playerPos, minDistance);
        GameObject goal = GameObject.CreatePrimitive(PrimitiveType.Cube);
        goal.name = "Goal";

        // APLICA A TEXTURA DA META
        goal.GetComponent<Renderer>().material = CreateTexturedMaterial("GoalTexture", Color.cyan);
        goal.transform.position = world.GridToWorld(p, 0.5f);

        Light goalLight = goal.AddComponent<Light>();
        goalLight.type = LightType.Point;
        goalLight.color = Color.cyan;
        goalLight.range = 15.0f;
        goalLight.intensity = 8.0f;

        // 🚨 ATUALIZADO: Agora usa o script unificado GameObjective (tipo ExitPortal)
        GameObjective obj = goal.AddComponent<GameObjective>();
        obj.gridPos = p;
        obj.type = ObjectiveType.ExitPortal;
    }

    public static void SpawnCollectibles(GridWorld world, System.Random rng, int count)
    {
        for (int i = 0; i < count; i++) {
            Vector2Int p = GetUniqueSpawnPosition(world, rng);
            // Passou de Esfera para Cubo para mapear a textura perfeitamente
            GameObject coin = GameObject.CreatePrimitive(PrimitiveType.Cube);
            coin.name = "Collectible";
            coin.tag = "Collectible"; // Mantemos a tag caso algum script precise de limpar a cena
            coin.transform.position = world.GridToWorld(p, 0.3f);
            coin.transform.localScale = Vector3.one * 0.5f;

            // APLICA A TEXTURA DA MOEDA
            coin.GetComponent<Renderer>().material = CreateTexturedMaterial("CollectibleTexture", Color.yellow);

            Light coinLight = coin.AddComponent<Light>();
            coinLight.type = LightType.Point;
            coinLight.color = Color.yellow;
            coinLight.range = 8.0f;
            coinLight.intensity = 5.0f;

            // 🚨 ATUALIZADO: Agora usa o script unificado GameObjective (tipo Coin)
            GameObjective obj = coin.AddComponent<GameObjective>();
            obj.gridPos = p;
            obj.type = ObjectiveType.Coin;

            coin.AddComponent<ItemAnimate>(); // Adiciona animação de rotação!
        }
    }

    public static void SpawnPowerUps(GridWorld world, System.Random rng, int count)
    {
        for (int i = 0; i < count; i++) {
            Vector2Int p = GetUniqueSpawnPosition(world, rng);
            PowerUpType selectedType = (rng.Next(0, 2) == 0) ? PowerUpType.Time : PowerUpType.Speed;

            GameObject item = GameObject.CreatePrimitive(PrimitiveType.Cube);
            item.name = "PowerUp_" + selectedType;
            item.tag = "Collectible";

            Color col = (selectedType == PowerUpType.Time) ? Color.blue : Color.magenta;

            // APLICA A TEXTURA DO POWERUP
            item.GetComponent<Renderer>().material = CreateTexturedMaterial("PowerUpTexture", col);

            item.transform.position = world.GridToWorld(p, 0.5f);
            item.transform.localScale = new Vector3(0.5f, 0.5f, 0.5f);

            PowerUp script = item.AddComponent<PowerUp>();
            script.type = selectedType;
            script.gridPos = p;

            item.GetComponent<Collider>().isTrigger = true;
            item.AddComponent<ItemAnimate>();
        }
    }

    public static void SpawnPhysicalExplosion(Vector3 position, Color color, int amount) {
        for (int i = 0; i < amount; i++) {
            GameObject p = GameObject.CreatePrimitive(PrimitiveType.Cube);
            p.transform.position = position + Random.insideUnitSphere * 0.5f;
            p.transform.localScale = Vector3.one * 0.2f;

            // Visual
            p.GetComponent<Renderer>().material = CreateSimpleMaterial(color);

            // Física 🚨
            Rigidbody rb = p.AddComponent<Rigidbody>();
            // Dá um impulso inicial aleatório para cima e para os lados
            Vector3 force = new Vector3(Random.Range(-2f, 2f), Random.Range(3f, 6f), Random.Range(-2f, 2f));
            rb.AddForce(force, ForceMode.Impulse);

            // Lógica de limpeza
            p.AddComponent<VoxelParticle>();
        }
    }

    public static void SpawnTraps(GridWorld world, System.Random rng, int count, float penalty) {
        for (int i = 0; i < count; i++) {
            Vector2Int p = GetUniqueSpawnPosition(world, rng);
            GameObject trapObj = GameObject.CreatePrimitive(PrimitiveType.Cube);
            trapObj.name = "Trap";
            trapObj.tag = "Collectible";

            // APLICA A TEXTURA DA ARMADILHA
            trapObj.GetComponent<Renderer>().material = CreateTexturedMaterial("TrapTexture", new Color(0.8f, 0.2f, 0.2f));
            trapObj.transform.position = world.GridToWorld(p, 0.05f);
            trapObj.transform.localScale = new Vector3(0.8f, 0.1f, 0.8f);

            Trap script = trapObj.AddComponent<Trap>();
            script.gridPos = p;
            script.penalty = penalty;
        }
    }
}