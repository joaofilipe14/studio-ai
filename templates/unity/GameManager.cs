using UnityEngine;
using System.Collections.Generic;
using System.IO; // Necessário para gravar o ficheiro de métricas

[System.Serializable]
public class GameMetrics
{
    public int total_rounds;
    public int wins;
    public int timeouts;
    public int stuck_events;
    public float win_rate;
    public float avg_time_to_goal;
    public string currentMode;
    public int total_collected;
}

public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }
    private GameGenome currentGenome;

    [Header("Configurações de Grelha (BuildScript)")]
    public int gridWidth = 15;
    public int gridHeight = 15;
    public float cellSize = 1f;
    public int obstacles = 25;
    public int collectibles = 5;
    public bool buildBorderWalls = true;

    [Header("Regras de Jogo")]
    public int seed;
    public float timeLimit = 25f;
    private float currentTimer; // Timer interno para não gastar a config original
    public int rounds = 5;
    private int currentRound = 0; // Contador de rondas atual
    public bool finished;
    [Header("Progresso da Ronda")]
    public string currentMode = "PointToPoint";
    private int collectedInRound = 0;

    [Header("Agente e Inimigo")]
    public float agentMoveSpeed = 4.5f;
    public bool userControl = false;
    public bool spawnChaser = true;
    public float chaserMoveSpeed = 3.5f;
    [Header("Power-ups")]
    public float timeBoostAmount = 5f;
    public float speedBoostMultiplier = 1.5f;
    public float speedBoostDuration = 3f;
    [Header("Métricas Internas")]
    private int winsCount = 0;
    private int timeoutsCount = 0;
    private int stuckCount = 0;
    private int totalCollectedGame = 0;
    private List<float> winTimes = new List<float>(); // Lista para calcular avg_time_to_goal
    [Header("Obstáculos")]
    public float obsMinScale = 1.0f;
    public float obsMaxScale = 1.0f;
    [Header("Referências")]
    public GridWorld world;
    public SimpleAgent agent;
    private HashSet<Vector2Int> occupiedCells = new HashSet<Vector2Int>();

    void Awake() {
        if (Instance == null) Instance = this;
        LoadGenomeConfig();
    }

    void Start() {
        StartNewRun();
        SetupAudio();
    }

    public void StartNewRun()
    {
        currentRound++;
        if (currentRound > rounds) {
            QuitGame();
            return;
        }

        finished = false;
        collectedInRound = 0;
        currentTimer = timeLimit; // Reinicia o cronómetro para a nova ronda

        if (world == null) world = gameObject.AddComponent<GridWorld>();

        int activeSeed = (currentGenome.seed == 0) ? (int)System.DateTime.UtcNow.Ticks : currentGenome.seed;
        int obstaclesToSpawn = currentGenome.obstacles.count;
        world.Build(gridWidth, gridHeight, cellSize, obstaclesToSpawn, activeSeed);

        CleanupScene();
        BuildFloorAndObstacles();
        SpawnEntities();
    }

    void SetupAudio() {
        GameObject musicObj = new GameObject("BackgroundMusic");
        AudioSource source = musicObj.AddComponent<AudioSource>();
        source.clip = Resources.Load<AudioClip>("Music/synthwave_loop");
        source.loop = true;
        source.playOnAwake = true;
        source.volume = 0.5f;
        source.Play();
    }

    void LoadGenomeConfig()
    {
        // Caminho para o ficheiro JSON (normalmente na pasta do projeto)
        string path = Path.Combine(Application.dataPath, "..", "game_genome.json");
        GameGenomeCollection collection = GameGenomeCollection.Load(path);

        userControl = collection.userControl;
        string activeModeName = string.IsNullOrEmpty(collection.mode) ? "PointToPoint" : collection.mode;
        currentGenome = collection.GetConfig(activeModeName);

        currentMode = currentGenome.mode;
        timeLimit = currentGenome.rules.timeLimit;
        rounds = currentGenome.rules.rounds;
        collectibles = currentGenome.rules.targetCount;
        agentMoveSpeed = currentGenome.agent.speed;
        chaserMoveSpeed = currentGenome.rules.enemySpeed;
        spawnChaser = chaserMoveSpeed > 0;
        obsMinScale = currentGenome.obstacles.minScale;
        obsMaxScale = currentGenome.obstacles.maxScale;
        // Ajusta o grid com base no tamanho da arena do Genome
        gridWidth = (int)(currentGenome.arena.halfSize * 2);
        gridHeight = (int)(currentGenome.arena.halfSize * 2);
    }

    Vector2Int GetUniqueSpawnPosition(System.Random rng)
    {
        for (int i = 0; i < 100; i++) {
            Vector2Int pos = world.RandomFreeCell(rng);
            // Se a célula ainda não estiver ocupada por uma entidade
            if (!occupiedCells.Contains(pos)) {
                occupiedCells.Add(pos); // Marca como ocupada
                return pos;
            }
        }
        // Fallback: Se o mapa estiver tão cheio que não encontra espaço (muito raro)
        return world.RandomFreeCell(rng);
    }

    void OnGUI() {
        GUI.Box(new Rect(10, 10, 250, 135), "ESTADO DA SIMULAÇÃO");
        GUI.Label(new Rect(20, 35, 230, 25), $"Modo: {currentMode}");
        GUI.Label(new Rect(20, 55, 230, 25), $"Ronda: {currentRound} / {rounds}");
        GUI.Label(new Rect(20, 75, 230, 25), $"Tempo: {currentTimer:F1}s");
        if (currentMode == "Collect") {
            GUI.Label(new Rect(20, 95, 230, 25), $"Moedas: {collectedInRound} / {collectibles}");
        } else if (currentMode == "PointToPoint") {
            GUI.Label(new Rect(20, 95, 230, 25), "Objetivo: Chegar à Meta!");
        }
        GUI.Label(new Rect(20, 115, 230, 25), $"Vitórias: {winsCount}");
        string textoControlo = userControl ? "Manual (Jogador)" : "IA (Automático)";
        GUI.Label(new Rect(20, 135, 230, 25), $"Controlo: {textoControlo}");
    }

    void BuildFloorAndObstacles() {
        var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Floor";
        floor.GetComponent<Renderer>().material = CreateSimpleMaterial(new Color(0.2f, 0.2f, 0.2f));
        floor.transform.localScale = new Vector3(gridWidth * cellSize / 10f, 1, gridHeight * cellSize / 10f);
        floor.transform.position = Vector3.zero;

        Material obsMat = CreateSimpleMaterial(new Color(0.4f, 0.4f, 0.6f));
        for (int x = 0; x < world.Width; x++) {
            for (int z = 0; z < world.Height; z++) {
                if (world.IsBlocked(new Vector2Int(x, z))) {
                    var obs = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    obs.name = "Obstacle_" + x + "_" + z;
                    obs.GetComponent<Renderer>().material = obsMat;
                    System.Random rng = new System.Random(seed);
                    float randomScale = (float)rng.NextDouble() * (obsMaxScale - obsMinScale) + obsMinScale;
                    obs.transform.localScale = Vector3.one * randomScale;
                    obs.transform.position = world.GridToWorld(new Vector2Int(x, z), randomScale / 2f);
                }
            }
        }
    }

    void SpawnEntities() {
        System.Random rng = new System.Random(seed);
        occupiedCells.Clear();
        Vector2Int start = GetUniqueSpawnPosition(rng);

        GameObject agentGO = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        agentGO.GetComponent<Renderer>().material = CreateSimpleMaterial(Color.green);
        agentGO.name = "Agent";
        agent = agentGO.AddComponent<SimpleAgent>();
        agent.world = world;
        agent.gridPos = start;
        agent.moveSpeed = agentMoveSpeed;
        agentGO.transform.position = world.GridToWorld(start);

        if (spawnChaser) {
            Vector2Int chaserStart = GetUniqueSpawnPosition(rng);
            GameObject chaserGO = GameObject.CreatePrimitive(PrimitiveType.Cube);
            chaserGO.name = "Chaser";

            // Define a cor vermelha para o perseguidor
            chaserGO.GetComponent<Renderer>().material = CreateSimpleMaterial(Color.red);

            ChaserAI ai = chaserGO.AddComponent<ChaserAI>();
            ai.world = world;
            ai.gridPos = chaserStart;
            ai.moveSpeed = chaserMoveSpeed; // Usa a velocidade definida no BuildScript
            chaserGO.transform.position = world.GridToWorld(chaserStart);
        }
        if (currentGenome.rules.powerUpChance > 0) {
            SpawnPowerUps(rng);
        }

        if (currentMode == "PointToPoint") {
            SpawnGoal(rng);
        } else {
            for (int i = 0; i < collectibles; i++) SpawnCollectible(rng);
        }
        if (currentGenome.rules.trapChance > 0) {
            SpawnTraps(rng);
        }
    }

    void SpawnGoal(System.Random rng) {
        Vector2Int p = GetUniqueSpawnPosition(rng);
        GameObject goal = GameObject.CreatePrimitive(PrimitiveType.Cube);
        goal.name = "Goal";
        goal.GetComponent<Renderer>().material = CreateSimpleMaterial(Color.cyan); // Bloco Azul
        goal.transform.position = world.GridToWorld(p, 0.5f);
        goal.AddComponent<Goal>().gridPos = p;
    }

    void SpawnCollectible(System.Random rng) {
        Vector2Int p = GetUniqueSpawnPosition(rng);
        GameObject coin = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        coin.name = "Collectible";
        coin.tag = "Collectible";
        coin.transform.position = world.GridToWorld(p, 0.3f);
        coin.transform.localScale = Vector3.one * 0.5f;
        coin.GetComponent<Renderer>().material.color = Color.yellow;
        coin.AddComponent<Collectible>().gridPos = p;
    }

   void SpawnPowerUps(System.Random rng) {
       int maxItems = Mathf.FloorToInt((gridWidth * gridHeight) * currentGenome.rules.powerUpChance * 0.1f);
       if (maxItems < 1 && currentGenome.rules.powerUpChance > 0) maxItems = 1;

       for (int i = 0; i < maxItems; i++) {
           Vector2Int p = GetUniqueSpawnPosition(rng);
           PowerUpType selectedType = (rng.Next(0, 2) == 0) ? PowerUpType.Time : PowerUpType.Speed;

           // CORREÇÃO: Usar Cylinder (Cilindro) que existe no Unity
           GameObject item = GameObject.CreatePrimitive(PrimitiveType.Cylinder);

           item.name = "PowerUp_" + selectedType;
           item.tag = "Collectible";

           Color col = (selectedType == PowerUpType.Time) ? Color.blue : Color.magenta;
           item.GetComponent<Renderer>().material = CreateSimpleMaterial(col);

           // Posicionamento e Rotação inicial para parecer um "disco" ou "token"
           item.transform.position = world.GridToWorld(p, 0.5f);
           item.transform.localScale = new Vector3(0.5f, 0.1f, 0.5f); // Fica achatado como uma moeda
           item.transform.rotation = Quaternion.Euler(90, 0, 0); // Fica de pé

           PowerUp script = item.AddComponent<PowerUp>();
           script.type = selectedType;
           script.gridPos = p;

           item.GetComponent<Collider>().isTrigger = true;

           // ADICIONAR ANIMAÇÃO: Faz o item rodar e flutuar
           item.AddComponent<ItemAnimate>();
       }
   }

   void SpawnTraps(System.Random rng) {
       int trapCount = Mathf.FloorToInt((gridWidth * gridHeight) * currentGenome.rules.trapChance);

       for (int i = 0; i < trapCount; i++) {
           Vector2Int p = GetUniqueSpawnPosition(rng); // Garante que não nasce em cima de moedas/agente

           GameObject trapObj = GameObject.CreatePrimitive(PrimitiveType.Cube);
           trapObj.name = "Trap";
           trapObj.tag = "Collectible"; // Para limpeza automática

           // Visual: Um tapete vermelho no chão
           trapObj.GetComponent<Renderer>().material = CreateSimpleMaterial(new Color(0.8f, 0.2f, 0.2f));
           trapObj.transform.position = world.GridToWorld(p, 0.05f); // Quase ao nível do chão
           trapObj.transform.localScale = new Vector3(0.8f, 0.1f, 0.8f);

           Trap script = trapObj.AddComponent<Trap>();
           script.gridPos = p;
           script.penalty = currentGenome.rules.trapPenalty;
       }
   }

    Material CreateSimpleMaterial(Color color) {
        Shader safetyShader = Shader.Find("Unlit/Color");
        if (safetyShader == null) safetyShader = Shader.Find("Legacy Shaders/VertexLit");
        Material mat = new Material(safetyShader);
        mat.color = color;
        return mat;
    }

    void Update() {
        if (finished) return;
        currentTimer -= Time.deltaTime; // Atualiza o cronómetro da ronda
        if (currentTimer <= 0) {
            currentTimer = 0;
            Lose("TEMPO ESGOTADO");
        }
    }

    public void OnGoalReached() {
        if (finished) return;
        finished = true;

        winsCount++; // Métrica de vitória
        winTimes.Add(timeLimit - currentTimer); // Regista o tempo gasto para chegar ao objetivo

        Debug.Log("Objetivo alcançado! Vitória.");
        Invoke("StartNewRun", 1.0f);
    }

    public void OnAgentCaught() {
        stuckCount++; // Se for apanhado ou ficar preso, conta como stuck_event
        StartNewRun();
    }

    void Lose(string reason) {
        if (finished) return;
        finished = true;

        timeoutsCount++; // Métrica de timeout
        Debug.Log(reason);
        Invoke("StartNewRun", 1.0f);
    }

    void CleanupScene() {
        foreach (var obj in GameObject.FindGameObjectsWithTag("Collectible")) Destroy(obj);
        GameObject[] allObjects = Object.FindObjectsByType<GameObject>(FindObjectsSortMode.None);
        foreach (var o in allObjects) {
            if (o.name.StartsWith("Obstacle_") || o.name == "Floor" || o.name == "Agent" || o.name == "Goal")
            {
                Destroy(o);
            }
        }
    }

    public void OnCollect(Vector2Int p) {
        if (finished) return;
        collectedInRound++;
        totalCollectedGame++;
        // No modo Collect, não spawna mais moedas. O Agente apanha as que já lá estão!
        if (collectedInRound >= collectibles) OnGoalReached();
    }

    public void AddExtraTime() {
        currentTimer += timeBoostAmount;
        Debug.Log("Power-up: +5s de tempo!");
    }

    // Método para o Power-up de Velocidade
    public void ApplySpeedBoost() {
        StartCoroutine(SpeedBoostRoutine());
    }

    public void ApplyTrapPenalty(float amount) {
        currentTimer -= amount;
        if (currentTimer < 0) currentTimer = 0;
        Debug.Log($"Armadilha! -{amount}s");
    }

    private System.Collections.IEnumerator SpeedBoostRoutine() {
        float originalSpeed = agent.moveSpeed;
        agent.moveSpeed *= speedBoostMultiplier;
        Debug.Log("Power-up: Velocidade aumentada!");
        yield return new WaitForSeconds(speedBoostDuration);
        agent.moveSpeed = originalSpeed;
        Debug.Log("Velocidade normalizada.");
    }

    void QuitGame() {
        // Cálculo final das métricas antes de sair
        GameMetrics metrics = new GameMetrics {
            total_rounds = rounds,
            wins = winsCount,
            timeouts = timeoutsCount,
            stuck_events = stuckCount,
            win_rate = rounds > 0 ? (float)winsCount / rounds : 0f,
            currentMode = this.currentMode,
            total_collected = this.totalCollectedGame
        };

        float sumTime = 0f;
        foreach (float t in winTimes) sumTime += t;
        metrics.avg_time_to_goal = winsCount > 0 ? (sumTime / winsCount) : 0f;

        // Gravação do ficheiro JSON na raiz do projeto
        string json = JsonUtility.ToJson(metrics, true);
        string path = Path.Combine(Application.dataPath, "..", "metrics.json");
        File.WriteAllText(path, json);

        Debug.Log($"Simulação concluída. Métricas exportadas para: {path}");

        #if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
        #else
            Application.Quit(0);
            System.Diagnostics.Process.GetCurrentProcess().Kill(); // Garante o fecho imediato em batch mode
        #endif
    }
}