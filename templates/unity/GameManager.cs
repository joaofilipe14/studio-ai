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

    [Header("Configurações Dinâmicas (Genome)")]
    private GameGenome currentGenome;
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

    void Awake()
    {
        if (Instance == null) Instance = this;

        // Caminho robusto para o Genoma
        string genomePath = Path.Combine(Application.dataPath, "..", "game_genome.json");
        if (!File.Exists(genomePath)) {
            genomePath = Path.Combine(Directory.GetCurrentDirectory(), "game_genome.json");
        }

        if (File.Exists(genomePath)) {
            currentGenome = GameGenome.Load(genomePath);
            Debug.Log($"Genoma carregado: {currentGenome.mode}");
        } else {
            Debug.LogError("ERRO: game_genome.json não encontrado!");
        }
    }

    void Start()
    {
        if (currentGenome != null) StartRound(round);
    }

    void Update()
    {
        if (currentGenome == null) return;

        timeLeft -= Time.deltaTime;
        if (timeLeft <= 0f)
        {
            Debug.Log($"TIME OUT (round {round})");
            timeoutsCount++;
            NextRound();
        }
    }

    public bool IsCollectMode() => currentGenome != null && currentGenome.mode == "Collect";

    public void OnCollectiblePickedUp()
    {
        coinsRemaining--;
        Debug.Log($"Item coletado! Restam: {coinsRemaining}");
        if (coinsRemaining <= 0) Win();
    }

    public void Win()
    {
        float timeTaken = currentGenome.rules.timeLimit - timeLeft;
        Debug.Log($"WIN round {round}! Tempo: {timeTaken:F2}s");

        winsCount++;
        winTimes.Add(timeTaken);
        NextRound();
    }

    public void NotifyStuck()
    {
        Debug.LogWarning("Agente ficou preso!");
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

        // Limpeza de segurança: Tags no Unity são sensíveis a maiúsculas
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
            SpawnEnemies(currentGenome.rules.targetCount / 2 + 1); // Exemplo de escala
        }
        if (agent != null)
        {
            // Reseta posição e reconfigura modo (IA vs User)
            agent.ResetAgent(new Vector3(0, 1f, 0), goal);
            agent.Configure(currentGenome.agent, goal);
        }
    }

    void SpawnEnemies(int count)
    {
        // Limpa inimigos antigos
        foreach (var e in activeEnemies) if (e != null) Destroy(e);
        activeEnemies.Clear();

        for (int i = 0; i < count; i++)
        {
            Vector3 pos = GetValidNavMeshPoint(currentGenome.arena.halfSize);
            GameObject enemy = GameObject.CreatePrimitive(PrimitiveType.Cube);
            enemy.name = "ChaserEnemy";
            enemy.GetComponent<BoxCollider>().isTrigger = true;
            enemy.transform.position = pos;
            enemy.GetComponent<Renderer>().material.color = Color.red;
            Rigidbody rb = enemy.AddComponent<Rigidbody>();
            rb.isKinematic = true; // Importante para não cair do chão, mas ainda detetar colisões
            enemy.GetComponent<BoxCollider>().isTrigger = false;
            // Adiciona lógica de perseguição
            var nav = enemy.AddComponent<NavMeshAgent>();
            nav.speed = currentGenome.rules.enemySpeed;

            // Adiciona um script simples de IA ao inimigo
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
                // Plano B: Se o prefab falhar, cria esfera visual
                coin = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                coin.transform.position = pos;
                coin.transform.localScale = Vector3.one * 0.6f;
                coin.GetComponent<Renderer>().material.color = Color.yellow;
            }

            coin.tag = "Collectible";
            var col = coin.GetComponent<Collider>();
            if (col != null) col.isTrigger = true;

            // Injeta o script se não existir
            if (coin.GetComponent<Collectible>() == null)
                coin.AddComponent<Collectible>();
        }
    }

    // Garante que o ponto gerado é acessível e não está dentro de cubos
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
        return new Vector3(0, 0.5f, 0); // Centro como última alternativa
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