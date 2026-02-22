using UnityEngine;
using UnityEngine.AI;
using System.IO;
using System.Collections.Generic;

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
    public static GameManager Instance;

    public enum GameState { Menu, Playing, GameOver }
    private GameState currentState = GameState.Menu;

    [Header("Configurações Dinâmicas (Genome)")]
    private GameGenomeCollection allGenomes; // A LISTA DE MODOS
    private GameGenome currentGenome;        // O MODO ATIVO
    private int coinsRemaining = 0;

    [Header("Inimigos (Fase 5)")]
    public GameObject enemyPrefab;
    private List<GameObject> activeEnemies = new List<GameObject>();

    [Header("Referências")]
    public SimpleAgent agent;
    public GameObject coinPrefab;
    public Transform goal;

    private float timeLeft;
    private int round = 1;
    private int winsCount = 0;
    private int timeoutsCount = 0;
    private int stuckCount = 0;
    private List<float> winTimes = new List<float>();

    private string hudText = "";
    private float menuTimer = 0f;
    private float autoClickDelay = 2.0f;
    private string autoSelectedMode = "PointToPoint";

    void Awake()
    {
        if (Instance == null) Instance = this;

        string genomePath = Path.Combine(Application.dataPath, "..", "game_genome.json");
        if (!File.Exists(genomePath)) {
            genomePath = Path.Combine(Directory.GetCurrentDirectory(), "game_genome.json");
        }

        // CARREGA A LISTA TODA
        allGenomes = GameGenomeCollection.Load(genomePath);

        if (allGenomes != null && allGenomes.configs != null && allGenomes.configs.Length > 0) {
            currentGenome = allGenomes.configs[0];
            autoSelectedMode = currentGenome.mode; // O auto-click vai escolher o primeiro da lista
        }
    }

    void Start()
    {
        currentState = GameState.Menu;
    }

    void Update()
    {
        if (currentGenome == null) return;

        if (currentState == GameState.Menu)
        {
            menuTimer += Time.deltaTime;
            if (menuTimer >= autoClickDelay)
            {
                Debug.Log($"[UI Agent] A clicar automaticamente no modo: {autoSelectedMode}");
                StartGame(autoSelectedMode);
            }
        }
        else if (currentState == GameState.Playing)
        {
            timeLeft -= Time.deltaTime;
            UpdateHUDString();

            if (timeLeft <= 0f)
            {
                timeoutsCount++;
                NextRound();
            }
        }
    }

    void UpdateHUDString()
    {
        string modeName = IsCollectMode() ? "Collect (Apanhar Moedas)" : "Point-to-Point (Fuga)";
        string coinsText = IsCollectMode() ? $"\nMOEDAS RESTANTES: {coinsRemaining}" : "";

        hudText = $"MODO: {modeName}\n" +
                  $"RONDA: {round} / {currentGenome.rules.rounds}\n" +
                  $"TEMPO: {Mathf.Max(0, timeLeft):F1}s" +
                  coinsText;
    }

    void OnGUI()
    {
        if (allGenomes == null || allGenomes.configs == null) return;

        GUIStyle style = new GUIStyle(GUI.skin.label);
        style.fontSize = 28;
        style.fontStyle = FontStyle.Bold;
        style.normal.textColor = Color.cyan;

        if (currentState == GameState.Menu)
        {
            GUIStyle btnStyle = new GUIStyle(GUI.skin.button);
            btnStyle.fontSize = 30;
            btnStyle.fontStyle = FontStyle.Bold;

            GUI.Label(new Rect(Screen.width / 2 - 200, Screen.height / 2 - 200, 400, 50), "SELECIONAR MODO DE JOGO", style);

            // DESENHA OS BOTÕES DINAMICAMENTE COM BASE NO JSON
            float yPos = Screen.height / 2 - 100;
            foreach (var config in allGenomes.configs)
            {
                Rect btnRect = new Rect(Screen.width / 2 - 200, yPos, 400, 80);
                if (GUI.Button(btnRect, config.mode.ToUpper(), btnStyle))
                {
                    StartGame(config.mode);
                }
                yPos += 100; // Espaço para o próximo botão
            }

            GUIStyle agentStyle = new GUIStyle(GUI.skin.label);
            agentStyle.fontSize = 20;
            agentStyle.normal.textColor = Color.yellow;
            float timeRemaining = Mathf.Max(0, autoClickDelay - menuTimer);
            GUI.Label(new Rect(Screen.width / 2 - 200, yPos + 50, 400, 50),
                $"UI Agent a auto-selecionar ({autoSelectedMode}) em {timeRemaining:F1}s...", agentStyle);
        }
        else if (currentState == GameState.Playing)
        {
            GUI.Label(new Rect(20, 20, 600, 200), hudText, style);
        }
    }

    public void StartGame(string selectedMode)
    {
        if (currentState != GameState.Menu) return;

        // VAI BUSCAR AS REGRAS ESPECÍFICAS DESTE MODO
        currentGenome = allGenomes.GetConfig(selectedMode);
        currentState = GameState.Playing;
        StartRound(round);
    }

    public bool IsCollectMode() => currentGenome != null && currentGenome.mode == "Collect";

    public void OnCollectiblePickedUp()
    {
        coinsRemaining--;
        if (coinsRemaining <= 0) Win();
    }

    public void Win()
    {
        float timeTaken = currentGenome.rules.timeLimit - timeLeft;
        winsCount++;
        winTimes.Add(timeTaken);
        NextRound();
    }

    public void NotifyStuck()
    {
        stuckCount++;
        NextRound();
    }

    void NextRound()
    {
        round++;
        if (round > currentGenome.rules.rounds)
            ExportMetricsAndQuit();
        else
            StartRound(round);
    }

    void StartRound(int r)
    {
        timeLeft = currentGenome.rules.timeLimit;

        foreach (var c in GameObject.FindGameObjectsWithTag("Collectible")) Destroy(c);

        if (IsCollectMode())
        {
            if (goal != null) goal.gameObject.SetActive(false);
            coinsRemaining = currentGenome.rules.targetCount;
            SpawnCollectibles(coinsRemaining);
        }
        else
        {
            if (goal != null)
            {
                goal.gameObject.SetActive(true);
                goal.position = GetValidNavMeshPoint(currentGenome.arena.halfSize);
            }
            coinsRemaining = 1;
        }

        if (currentGenome.rules.enemySpeed > 0)
        {
            SpawnEnemies(currentGenome.rules.targetCount / 2 + 1);
        }

        if (agent != null)
        {
            agent.ResetAgent(new Vector3(0, 1f, 0), goal);
            agent.Configure(currentGenome.agent, goal);
        }
    }

    void SpawnEnemies(int count)
    {
        foreach (var e in activeEnemies) if (e != null) Destroy(e);
        activeEnemies.Clear();

        for (int i = 0; i < count; i++)
        {
            Vector3 pos = GetValidNavMeshPoint(currentGenome.arena.halfSize);
            GameObject enemy = GameObject.CreatePrimitive(PrimitiveType.Cube);
            enemy.name = "ChaserEnemy";
            enemy.GetComponent<BoxCollider>().isTrigger = true;
            enemy.transform.position = pos;

            var mat = enemy.GetComponent<Renderer>().material;
            mat.color = Color.red;
            mat.EnableKeyword("_EMISSION");
            mat.SetColor("_EmissionColor", Color.red * 2.5f);

            Rigidbody rb = enemy.AddComponent<Rigidbody>();
            rb.isKinematic = true;

            var nav = enemy.AddComponent<NavMeshAgent>();
            nav.speed = currentGenome.rules.enemySpeed;

            var ai = enemy.AddComponent<ChaserAI>();
            ai.target = agent.transform;

            activeEnemies.Add(enemy);
        }
    }

    void SpawnCollectibles(int count)
    {
        for (int i = 0; i < count; i++)
        {
            Vector3 pos = GetValidNavMeshPoint(currentGenome.arena.halfSize);
            GameObject coin;

            if (coinPrefab != null) {
                coin = Instantiate(coinPrefab, pos, Quaternion.identity);
            } else {
                coin = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                coin.transform.position = pos;
                coin.transform.localScale = Vector3.one * 0.6f;

                var mat = coin.GetComponent<Renderer>().material;
                mat.color = Color.yellow;
                mat.EnableKeyword("_EMISSION");
                mat.SetColor("_EmissionColor", Color.yellow * 2.5f);
            }

            coin.tag = "Collectible";
            var col = coin.GetComponent<Collider>();
            if (col != null) col.isTrigger = true;

            if (coin.GetComponent<Collectible>() == null)
                coin.AddComponent<Collectible>();
        }
    }

    Vector3 GetValidNavMeshPoint(float halfSize)
    {
        for (int i = 0; i < 50; i++)
        {
            float x = Random.Range(-halfSize + 1.5f, halfSize - 1.5f);
            float z = Random.Range(-halfSize + 1.5f, halfSize - 1.5f);
            Vector3 randomPos = new Vector3(x, 0.5f, z);

            if (NavMesh.SamplePosition(randomPos, out NavMeshHit hit, 2.0f, NavMesh.AllAreas))
            {
                return hit.position;
            }
        }
        return new Vector3(0, 0.5f, 0);
    }

    void ExportMetricsAndQuit()
    {
        GameMetrics metrics = new GameMetrics {
            total_rounds = currentGenome.rules.rounds,
            wins = winsCount,
            timeouts = timeoutsCount,
            stuck_events = stuckCount,
            win_rate = (float)winsCount / currentGenome.rules.rounds
        };

        float sumTime = 0f;
        foreach (float t in winTimes) sumTime += t;
        metrics.avg_time_to_goal = winsCount > 0 ? (sumTime / winsCount) : 0f;

        string json = JsonUtility.ToJson(metrics, true);
        File.WriteAllText(Path.Combine(Application.dataPath, "..", "metrics.json"), json);

        Debug.Log("Simulação concluída. Métricas exportadas.");

#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#else
        Application.Quit(0);
        System.Diagnostics.Process.GetCurrentProcess().Kill();
#endif
    }
}