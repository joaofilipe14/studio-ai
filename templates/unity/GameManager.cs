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
    private int collectedInRound = 0;

    [Header("Agente e Inimigo")]
    public float agentMoveSpeed = 4.5f;
    public bool userControl = false;
    public bool spawnChaser = true;
    public float chaserMoveSpeed = 3.5f;

    [Header("Métricas Internas")]
    private int winsCount = 0;
    private int timeoutsCount = 0;
    private int stuckCount = 0;
    private List<float> winTimes = new List<float>(); // Lista para calcular avg_time_to_goal

    [Header("Referências")]
    public GridWorld world;
    public SimpleAgent agent;

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
        float obstacleFill = (float)currentGenome.obstacles.count / (gridWidth * gridHeight);
        world.Build(gridWidth, gridHeight, cellSize, obstacleFill, seed);

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

        // Seleciona o modo (ou o primeiro disponível)
        currentGenome = collection.configs[0];

        // Sincroniza as variáveis do GameManager com o Genome
        timeLimit = currentGenome.rules.timeLimit;
        rounds = currentGenome.rules.rounds;
        collectibles = currentGenome.rules.targetCount;
        agentMoveSpeed = currentGenome.agent.speed;
        chaserMoveSpeed = currentGenome.rules.enemySpeed;
        spawnChaser = chaserMoveSpeed > 0;

        // Ajusta o grid com base no tamanho da arena do Genome
        gridWidth = (int)(currentGenome.arena.halfSize * 2);
        gridHeight = (int)(currentGenome.arena.halfSize * 2);
    }

    void OnGUI()
        {
            // Cria uma caixa de fundo para as informações
            GUI.Box(new Rect(10, 10, 250, 110), "ESTADO DA SIMULAÇÃO");

            GUI.Label(new Rect(20, 35, 230, 25), $"Ronda: {currentRound} / {rounds}");
            GUI.Label(new Rect(20, 55, 230, 25), $"Tempo: {currentTimer:F1}s");
            GUI.Label(new Rect(20, 75, 230, 25), $"Moedas: {collectedInRound} / {collectibles}");
            GUI.Label(new Rect(20, 95, 230, 25), $"Pontos Totais: {winsCount}");
        }

    void BuildFloorAndObstacles()
    {
        var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Floor";
        floor.GetComponent<Renderer>().material = CreateSimpleMaterial(new Color(0.2f, 0.2f, 0.2f));
        floor.transform.localScale = new Vector3(gridWidth * cellSize / 10f, 1, gridHeight * cellSize / 10f);
        floor.transform.position = Vector3.zero;

        Material obsMat = CreateSimpleMaterial(new Color(0.4f, 0.4f, 0.6f));
        for (int x = 0; x < world.Width; x++)
        {
            for (int z = 0; z < world.Height; z++)
            {
                if (world.IsBlocked(new Vector2Int(x, z)))
                {
                    var obs = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    obs.name = "Obstacle_" + x + "_" + z;
                    obs.GetComponent<Renderer>().material = obsMat;
                    obs.transform.position = world.GridToWorld(new Vector2Int(x, z), 0.5f);
                }
            }
        }
    }

    void SpawnEntities()
    {
        System.Random rng = new System.Random(seed);
        Vector2Int start = world.RandomFreeCell(rng);

        GameObject agentGO = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        agentGO.GetComponent<Renderer>().material = CreateSimpleMaterial(Color.green);
        agentGO.name = "Agent";
        agent = agentGO.AddComponent<SimpleAgent>();
        agent.world = world;
        agent.gridPos = start;
        agentGO.transform.position = world.GridToWorld(start);

        if (spawnChaser)
        {
            Vector2Int chaserStart = world.RandomFreeCell(rng);
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

        SpawnCollectible(rng);
    }

    void SpawnCollectible(System.Random rng)
    {
        Vector2Int p = world.RandomFreeCell(rng);
        GameObject coin = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        coin.name = "Collectible";
        coin.tag = "Collectible";
        coin.transform.position = world.GridToWorld(p, 0.3f);
        coin.transform.localScale = Vector3.one * 0.5f;
        coin.GetComponent<Renderer>().material.color = Color.yellow;
        coin.AddComponent<Collectible>().gridPos = p;
    }

    Material CreateSimpleMaterial(Color color)
    {
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

    public void OnGoalReached()
    {
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

    void CleanupScene()
    {
        foreach (var obj in GameObject.FindGameObjectsWithTag("Collectible")) Destroy(obj);
        GameObject[] allObjects = Object.FindObjectsByType<GameObject>(FindObjectsSortMode.None);
        foreach (var o in allObjects)
        {
            if (o.name.StartsWith("Obstacle_") || o.name == "Floor" || o.name == "Agent" || o.name == "Goal")
            {
                Destroy(o);
            }
        }
    }

    public void OnCollect(Vector2Int p)
        {
            if (finished) return;

            collectedInRound++;
            Debug.Log($"Moeda coletada! ({collectedInRound}/{collectibles})");

            // Se ainda não apanhámos todas as moedas desta ronda
            if (collectedInRound < collectibles)
            {
                // Spawnamos a próxima moeda
                System.Random rng = new System.Random((int)System.DateTime.UtcNow.Ticks + collectedInRound);
                SpawnCollectible(rng);
            }
            else
            {
                // Se já apanhámos todas, ganhámos a ronda!
                OnGoalReached();
            }
        }

    void QuitGame()
    {
        // Cálculo final das métricas antes de sair
        GameMetrics metrics = new GameMetrics {
            total_rounds = rounds,
            wins = winsCount,
            timeouts = timeoutsCount,
            stuck_events = stuckCount,
            win_rate = rounds > 0 ? (float)winsCount / rounds : 0f
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