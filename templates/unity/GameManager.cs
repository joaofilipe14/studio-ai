using UnityEngine;
using System.Collections.Generic;
using System.IO;

[System.Serializable]
public class LevelReport
{
    public int level_id;
    public string mode;
    public int total_rounds;
    public int wins;
    public float win_rate;
    public float avg_time_to_goal;
    public int stuck_events;
}

[System.Serializable]
public class CampaignMetrics
{
    public bool campaign_completed; // Chegou ao fim do nível 10?
    public int bottleneck_level;
    public bool is_human;
    public List<LevelReport> level_reports = new List<LevelReport>();
}

public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    // ==========================================
    // SISTEMA DE CAMPANHA (NOVO!)
    // ==========================================
    public List<LevelGenome> campaignData = new List<LevelGenome>();
    public int currentLevelIndex = 0; // Controla em que nível da array estamos

    // Propriedade que devolve sempre o nível correto
    public LevelGenome currentLevel {
        get {
            if (campaignData != null && currentLevelIndex < campaignData.Count)
                return campaignData[currentLevelIndex];
            return null;
        }
    }

    public PlayerSave currentPlayer { get; private set; }
    public CharacterClass selectedClass { get; private set; }
    public Roster roster { get; private set; }
    private bool isPaused = false;

    [Header("Configurações de Grelha")]
    public int gridWidth = 15;
    public int gridHeight = 15;
    public float cellSize = 1f;
    public int collectibles = 5;

    [Header("Regras de Jogo")]
    public int seed;
    public int currentActiveSeed;
    public float timeLimit = 25f;
    public float currentTimer;
    public int rounds = 30; // Limite de tentativas globais de segurança para o Bot
    private int totalAttempts = 0;
    public bool finished;
    public bool isPlaying = false;

    [Header("Progresso da Ronda")]
    public string currentMode = "PointToPoint";
    public int collectedInRound = 0;

    [Header("Agente e Inimigo")]
    public float agentMoveSpeed = 4.5f;
    public bool userControl = true;
    public float chaserMoveSpeed = 3.5f;

    [Header("Power-ups")]
    public float timeBoostAmount = 5f;
    public float speedBoostMultiplier = 1.5f;
    public float speedBoostDuration = 3f;

    [Header("Métricas Internas")]
    private int winsCount = 0;
    private int timeoutsCount = 0;
    private int stuckCount = 0;
    public int trapsHitCount = 0;
    private int totalCollectedGame = 0;
    private float totalPlayTime = 0f;
    private float roundPlayTime = 0f;

    [Header("Relatório Global")]
    public CampaignMetrics globalMetrics = new CampaignMetrics();

    [Header("Referências")]
    public GridWorld world;
    public SimpleAgent agent;

    [Header("Regras da Campanha")]
    public int botMaxAttempts = 10; // O Bot tem mais margem para testar exaustivamente
    public int currentLevelAttempts = 0;

    [Header("Áudio e SFX")]
    private AudioSource sfxSource;

    void Awake() {
        if (Instance == null) Instance = this;
        if (gameObject.GetComponent<UIManager>() == null) gameObject.AddComponent<UIManager>();
        LoadGenomeConfig();
    }

    void Start() { }

    public void StartNewRun() {
        totalAttempts++;
        if (totalAttempts > rounds || currentLevel == null) { QuitGame(); return; }

        currentLevelAttempts++; // Conta logo a tentativa 1 antes de jogares!
        roundPlayTime = 0f;     // Zera o relógio da ronda

        finished = false;
        isPlaying = true;
        collectedInRound = 0;

        currentMode = currentLevel.mode;
        Debug.Log($"Current mode: {currentMode}");
        timeLimit = currentLevel.rules.timeLimit;
        if (timeLimit <= 0.1f) timeLimit = 30f;
        collectibles = currentLevel.rules.targetCount;
        chaserMoveSpeed = currentLevel.rules.enemySpeed;
        gridWidth = (int)(currentLevel.arena.halfSize * 2);
        gridHeight = (int)(currentLevel.arena.halfSize * 2);
        seed = currentLevel.seed;
        agentMoveSpeed = selectedClass.stats.speed;

        currentTimer = timeLimit;

        // 🚨 SEMENTES DINÂMICAS (ROGUELIKE)
        // 1ª Tentativa = O Labirinto Original do Genoma.
        // Tentativas Seguintes = Gera uma semente caótica! Labirinto novo!
        if (currentLevelAttempts <= 1) {
            currentActiveSeed = seed;
        } else {
            currentActiveSeed = seed + UnityEngine.Random.Range(1000, 99999);
        }

        Debug.Log($"A iniciar Nível {currentLevel.level_id} | Semente Ativa: {currentActiveSeed} | Obstáculos: {currentLevel.obstacles.count}");

        if (!Application.isBatchMode && GameObject.Find("BackgroundMusic") == null) SetupAudio();

        if (world == null) world = gameObject.AddComponent<GridWorld>();

        // 🚨 O Mundo 3D usa agora a Semente Dinâmica
        world.Build(gridWidth, gridHeight, cellSize, currentLevel.obstacles.count, currentActiveSeed);

        CleanupScene();
        BuildFloorAndObstacles();

        // 🚨 A colocação dos itens também muda de sítio com a nova Semente!
        System.Random rng = new System.Random(currentActiveSeed);
        LevelSpawner.ResetSpawns();

        float vRadius = selectedClass != null ? selectedClass.stats.visionRadius : 8.0f;
        string spriteToLoad = selectedClass != null ? selectedClass.spriteName : "PlayerSprite";
        if (agent == null) {
            agent = LevelSpawner.SpawnAgent(world, rng, agentMoveSpeed, userControl, vRadius, spriteToLoad);
        } else {
            Vector2Int newStart = LevelSpawner.GetUniqueSpawnPosition(world, rng);
            agent.world = world;
            agent.moveSpeed = agentMoveSpeed;
            agent.ResetPosition(newStart);
        }
       LevelSpawner.CalculateReachableArea(world, agent.gridPos);

       float minGoalDistance = Mathf.Max(gridWidth, gridHeight) * 0.4f;
       float minEnemySafeDistance = Mathf.Max(gridWidth, gridHeight) * 0.3f;

        if (currentLevel.rules.enemyCount > 0)
            LevelSpawner.SpawnEnemies(world, rng, currentLevel.rules.enemyCount, chaserMoveSpeed, agent.gridPos, minEnemySafeDistance);

        if (currentMode == "PointToPoint")
            LevelSpawner.SpawnGoal(world, rng, agent.gridPos, minGoalDistance);
        else
            LevelSpawner.SpawnCollectibles(world, rng, collectibles);

        if (currentLevel.rules.powerUpCount > 0)
            LevelSpawner.SpawnPowerUps(world, rng, currentLevel.rules.powerUpCount);

        if (currentLevel.rules.trapCount > 0)
            LevelSpawner.SpawnTraps(world, rng, currentLevel.rules.trapCount, currentLevel.rules.trapPenalty);
        if (userControl) {
            Cursor.visible = false;
            Cursor.lockState = CursorLockMode.Locked;
        }
    }

    public void ResetTotalProgress() {
        string savePath = Path.Combine(Application.dataPath, "..", "player_save.json");
        if (File.Exists(savePath)) {
            File.Delete(savePath); // Apaga o ficheiro físico
            Debug.Log("Ficheiro de Save apagado. Reiniciando progresso...");
        }
        // Recarrega as configurações base (o LoadGenomeConfig já cria um save novo se não existir)
        LoadGenomeConfig();
        // Volta ao Menu Principal com os dados limpos
        UI_ReturnToMenu();
    }

    public void SetSelectedClass(CharacterClass newClass) {
        selectedClass = newClass;
        if (currentPlayer != null && currentPlayer.loadout != null) {
            currentPlayer.loadout.selectedClassID = newClass.id;
            string savePath = Path.Combine(Application.dataPath, "..", "player_save.json");
            currentPlayer.Save(savePath);
        }
    }

    void BuildFloorAndObstacles() {
        var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Floor";
        floor.GetComponent<Renderer>().material = CreateEnvironmentMaterial("FloorTexture", new Color(0.2f, 0.2f, 0.2f));

        float sizeX = gridWidth * cellSize;
        float sizeZ = gridHeight * cellSize;
        floor.transform.localScale = new Vector3(sizeX / 10f, 1, sizeZ / 10f);

        float centerX = (sizeX / 2f) - (cellSize / 2f);
        float centerZ = (sizeZ / 2f) - (cellSize / 2f);
        floor.transform.position = new Vector3(centerX, 0, centerZ);

        Material obsMat = CreateEnvironmentMaterial("ObstacleTexture", new Color(0.4f, 0.4f, 0.6f));

        for (int x = 0; x < world.Width; x++) {
            for (int z = 0; z < world.Height; z++) {
                if (world.IsBlocked(new Vector2Int(x, z))) {
                    var obs = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    obs.name = "Obstacle_" + x + "_" + z;
                    obs.GetComponent<Renderer>().material = obsMat;

                    System.Random rng = new System.Random(currentActiveSeed + x + z);
                    float randomScale = (float)rng.NextDouble() * (currentLevel.obstacles.maxScale - currentLevel.obstacles.minScale) + currentLevel.obstacles.minScale;

                    obs.transform.localScale = new Vector3(0.9f * cellSize, randomScale, 0.9f * cellSize);
                    obs.transform.position = world.GridToWorld(new Vector2Int(x, z), randomScale / 2f);
                }
            }
        }
    }

    Material CreateEnvironmentMaterial(string textureName, Color fallbackColor) {
        // 1. Volta a carregar a tua imagem da pasta Resources/Textures/
        Texture2D tex = Resources.Load<Texture2D>("Textures/" + textureName);

        // 2. Usamos o shader Standard (que aceita texturas e cores)
         Shader safetyShader = Shader.Find("Unlit/Color");
         if (safetyShader == null) safetyShader = Shader.Find("Legacy Shaders/VertexLit");
        Material mat = new Material(safetyShader);

        // 3. Aplica as cores do tema Cyberpunk como "Tinta" por cima da textura
        if (currentLevel != null && currentLevel.theme == "Cyberpunk Neon") {
            if (textureName == "FloorTexture") ColorUtility.TryParseHtmlString("#111111", out fallbackColor); // Cinza muito escuro
            else if (textureName == "ObstacleTexture") ColorUtility.TryParseHtmlString("#00ffff", out fallbackColor); // Ciano
        }

        mat.color = fallbackColor;

        // 4. Se a textura existir, aplica-a!
        if (tex != null) {
            mat.mainTexture = tex;
            // Repete a textura do chão para não ficar esticada e borrada num mapa gigante
            if (textureName == "FloorTexture") {
                mat.mainTextureScale = new Vector2(gridWidth / 4f, gridHeight / 4f);
            }
        }

        mat.SetFloat("_Glossiness", 0.2f); // Um bocadinho de reflexo para o estilo Neon
        return mat;
    }

    void LoadGenomeConfig() {
        // AGORA LÊ A CAMPANHA INTEIRA!
        string campaignPath = Path.Combine(Application.dataPath, "..", "level_genome.json");
        string rosterPath = Path.Combine(Application.dataPath, "..", "roster.json");
        string savePath = Path.Combine(Application.dataPath, "..", "player_save.json");

        roster = Roster.Load(rosterPath);
        currentPlayer = PlayerSave.Load(savePath);

        if (File.Exists(campaignPath)) {
            string json = File.ReadAllText(campaignPath);
            LevelGenome[] loadedLevels = JsonHelper.FromJson<LevelGenome>(json);
            if (loadedLevels != null && loadedLevels.Length > 0) {
                campaignData = new List<LevelGenome>(loadedLevels);
            }
        }

        // Blindagem de Emergência
        if (campaignData.Count == 0) {
            Debug.LogWarning("campaign.json não encontrado! A usar Nível de Emergência.");
            campaignData.Add(new LevelGenome {
                level_id = 1, mode = "PointToPoint", theme = "Cyberpunk Neon", seed = 1234,
                arena = new LevelArena { halfSize = 10f, walls = true },
                obstacles = new LevelObstacles { count = 50, minScale = 1f, maxScale = 1.5f },
                rules = new LevelRules { timeLimit = 60f, targetCount = 1, enemyCount = 1, enemySpeed = 2f }
            });
        }

        if (roster != null && currentPlayer != null && currentPlayer.loadout != null)
            selectedClass = roster.classes.Find(c => c.id == currentPlayer.loadout.selectedClassID);

        if (selectedClass == null) {
            selectedClass = new CharacterClass {
                name = "Desconhecido", spriteName = "PlayerSprite",
                stats = new CharacterStats { speed = 6f, acceleration = 12f, visionRadius = 8f, trapResistance = 1f }
            };
        }
        if (currentPlayer != null && campaignData.Count > 0) {
            // Se o save diz que estamos no Nível 2 (currentCampaignLevel = 2), o index tem de ser 1.
            currentLevelIndex = Mathf.Clamp(currentPlayer.currentCampaignLevel - 1, 0, campaignData.Count - 1);
            Debug.Log($"[Save Loaded] A arrancar a Campanha no Index {currentLevelIndex} (Nível {currentPlayer.currentCampaignLevel})");
        }

        userControl = !Application.isBatchMode;
    }

    void SetupAudio() {
        GameObject musicObj = GameObject.Find("BackgroundMusic") ?? new GameObject("BackgroundMusic");
        AudioSource musicSource = musicObj.GetComponent<AudioSource>() ?? musicObj.AddComponent<AudioSource>();
        musicSource.clip = Resources.Load<AudioClip>("Music/bg_theme"); // Nome atualizado para o novo sistema
        musicSource.loop = true;
        musicSource.volume = 0.4f;
        if (!musicSource.isPlaying) musicSource.Play();

        // 🚨 NOVO: Canal de Efeitos Sonoros (SFX)
        if (sfxSource == null) {
            GameObject sfxObj = new GameObject("SFXPlayer");
            sfxSource = sfxObj.AddComponent<AudioSource>();
        }
    }

    public void PlaySFX(string clipName) {
        AudioClip clip = Resources.Load<AudioClip>("Music/" + clipName);
        if (clip != null && sfxSource != null) {
            sfxSource.PlayOneShot(clip);
        }
    }

    void Update() {
        if (Input.GetKeyDown(KeyCode.Escape) && isPlaying && !finished) {
            TogglePause();
        }
        if (!isPlaying || finished || isPaused) return;
        totalPlayTime += Time.deltaTime;
        roundPlayTime += Time.deltaTime;
        currentTimer -= Time.deltaTime;
        if (currentTimer <= 0) {
            currentTimer = 0;
            Lose("TEMPO ESGOTADO");
        }
    }

    public void TogglePause() {
        isPaused = !isPaused;

        if (isPaused) {
            Time.timeScale = 0f; // Congela o motor de física e timers
            UIManager.Instance.ShowPauseMenu();
        } else {
            Time.timeScale = 1f; // Retoma o tempo normal
            UIManager.Instance.ShowHUD();
            // Bloqueia o rato de volta se for modo humano
            if (userControl) {
                Cursor.visible = false;
                Cursor.lockState = CursorLockMode.Locked;
            }
        }
    }

    public void OnGoalReached() {
        if (finished) return;
        //PlaySFX("sfx_win");
        finished = true;
        isPlaying = false;
        winsCount++;

        // 🚨 LOG MODO DEV (Vai para o Terminal Python)
        Debug.Log($"[ROUND STATS] Nível: {currentLevel.level_id} | Tentativa: {currentLevelAttempts} | Resultado: VITÓRIA | Tempo: {roundPlayTime:F1}s | Moedas: {collectedInRound}");

        string statsMsg = $"Nível {currentLevel.level_id} Concluído!\nTempo Usado: {roundPlayTime:F1}s\nMoedas: {collectedInRound}";
        // 1. GUARDA O RELATÓRIO DESTE NÍVEL ANTES DE AVANÇAR
        globalMetrics.level_reports.Add(new LevelReport {
            level_id = currentLevel != null ? currentLevel.level_id : 1,
            mode = this.currentMode,
            total_rounds = currentLevelAttempts,
            wins = 1, // Ganhou esta ronda
            win_rate = currentLevelAttempts > 0 ? 1f / currentLevelAttempts : 0f,
            avg_time_to_goal = currentLevelAttempts > 0 ? (totalPlayTime / currentLevelAttempts) : 0f,
            stuck_events = stuckCount
        });

        currentLevelIndex++; // Avança na Campanha
        if (userControl && currentPlayer != null) {
            currentPlayer.wallet.totalCoins += collectedInRound; // Enche a carteira!
            currentPlayer.stats.totalWins++;
            currentPlayer.currentCampaignLevel = Mathf.Max(currentPlayer.currentCampaignLevel, currentLevelIndex + 1);
            currentPlayer.Save(Path.Combine(Application.dataPath, "..", "player_save.json"));
        }

        // Limpa as variáveis para o NOVO nível
        currentLevelAttempts = 0;
        stuckCount = 0;
        totalPlayTime = 0f;

        // 2. LÓGICA DE CONTINUAÇÃO
        if (currentLevelIndex >= campaignData.Count) {
            globalMetrics.campaign_completed = true; // 🎉 SUCESSO TOTAL!
            globalMetrics.bottleneck_level = 0;

            if (userControl && UIManager.Instance != null) UIManager.Instance.ShowEndScreen(true, "CAMPANHA CONCLUÍDA! És uma Lenda!");
            else QuitGame();
        } else {
            if (userControl && UIManager.Instance != null) UIManager.Instance.ShowEndScreen(true, "Nível Concluído! Prepara-te para o próximo.");
            else Invoke("StartNewRun", 0.05f);
        }
    }

    // 💀 QUANDO MORRES, REINICIAS O MESMO NÍVEL (O index não sobe)
    public void OnAgentCaught() {
        if (finished) return;
        PlaySFX("sfx_lose");
        finished = true;
        isPlaying = false;
        stuckCount++;
        Debug.Log($"[ROUND STATS] Nível: {currentLevel.level_id} | Tentativa: {currentLevelAttempts} | Resultado: MORTO | Sobreviveu: {roundPlayTime:F1}s | Moedas: {collectedInRound}");
        if (!userControl) {
            // LÓGICA DO BOT (Testador)
            if (currentLevelAttempts >= botMaxAttempts) {
                Debug.Log($"[BOT] Nível {currentLevel.level_id} é impossível! A abortar...");
                QuitGame(); // Fecha para o Python corrigir o nível!
            } else {
                Invoke("StartNewRun", 0.05f); // Bot tenta outra vez rápido
            }
        } else {
            if (Camera.main != null) {
                var cam = Camera.main.GetComponent<CameraController>();
                if (cam != null) cam.TriggerShake(0.5f, 0.6f);
            }
            // 🚨 FIX: Ficas com as moedas que conseguiste apanhar antes de morrer!
            currentPlayer.wallet.totalCoins += collectedInRound;
            currentPlayer.stats.currentLives--; // Perde uma vida!

            if (currentPlayer.stats.currentLives <= 0) {
                currentPlayer.stats.currentLives = currentPlayer.stats.maxLives;
                currentPlayer.currentCampaignLevel = 1;
                currentPlayer.Save(Path.Combine(Application.dataPath, "..", "player_save.json"));

                if (UIManager.Instance != null) UIManager.Instance.ShowEndScreen(false, $"GAME OVER no Nível {currentLevel.level_id}!\nFicaste sem vidas.");
            } else {
                currentPlayer.Save(Path.Combine(Application.dataPath, "..", "player_save.json"));
                if (UIManager.Instance != null) UIManager.Instance.ShowEndScreen(false, $"Morreste no Nível {currentLevel.level_id}!\nVidas restantes: {currentPlayer.stats.currentLives}");
            }
        }
    }

    void Lose(string reason) {
        if (finished) return;
        PlaySFX("sfx_lose");
        Debug.Log("Perdeu!");
        finished = true;
        isPlaying = false;
        timeoutsCount++;
        Debug.Log($"[ROUND STATS] Nível: {currentLevel.level_id} | Tentativa: {currentLevelAttempts} | Resultado: TIMEOUT | Sobreviveu: {roundPlayTime:F1}s | Moedas: {collectedInRound}");
        if (userControl && currentPlayer != null) {
            currentPlayer.wallet.totalCoins += collectedInRound;
            currentPlayer.Save(Path.Combine(Application.dataPath, "..", "player_save.json"));
        }

        if (userControl && UIManager.Instance != null) UIManager.Instance.ShowEndScreen(false, $"Falhaste o Nível {currentLevel.level_id}!\nMotivo: {reason}");
        else Invoke("StartNewRun", 0.05f);
    }

   void CleanupScene() {
       foreach (var obj in GameObject.FindGameObjectsWithTag("Collectible")) Destroy(obj);
       GameObject[] allObjects = Object.FindObjectsByType<GameObject>(FindObjectsSortMode.None);
       foreach (var o in allObjects) {
           if (o.name.StartsWith("Obstacle_") || o.name == "Floor" || o.name == "Goal" || o.name.StartsWith("Chaser_"))
               Destroy(o);
       }
   }

    public void OnCollect(Vector2Int p) {
        if (finished) return;
        Vector3 worldPos = world.GridToWorld(p, 0.5f);
        LevelSpawner.SpawnPhysicalExplosion(worldPos, Color.yellow, 6);
        PlaySFX("sfx_coin");
        collectedInRound++;
        totalCollectedGame++;
        if (collectedInRound >= collectibles) OnGoalReached();
    }

    public void AddExtraTime() { currentTimer += timeBoostAmount; }
    public void ApplySpeedBoost() { StartCoroutine(SpeedBoostRoutine()); }

    public void ApplyTrapPenalty(float amount) {
        float resistance = selectedClass != null ? selectedClass.stats.trapResistance : 1.0f;
        currentTimer -= (amount * resistance);
        trapsHitCount++;
        if (currentTimer < 0) currentTimer = 0;
        if (Camera.main != null) {
            var cam = Camera.main.GetComponent<CameraController>();
            if (cam != null) cam.TriggerShake(0.2f, 0.3f);
        }
    }

    private System.Collections.IEnumerator SpeedBoostRoutine() {
        float originalSpeed = agent.moveSpeed;
        agent.moveSpeed *= speedBoostMultiplier;
        yield return new WaitForSeconds(speedBoostDuration);
        agent.moveSpeed = originalSpeed;
    }

    public void UI_PlayNextLevel() {
        if (UIManager.Instance != null) {
            UIManager.Instance.ShowHUD(); // Volta a colocar o Timer e as Moedas no ecrã!
        }
        StartNewRun();
    }

    public void UI_ReturnToMenu() {
        Time.timeScale = 1f; // 🚨 Garante que o jogo não fica "congelado" no menu
        isPaused = false;
        if (UIManager.Instance != null) {
            UIManager.Instance.ShowTitleScreen(); // Abre o Menu Principal
        }
        CleanupScene();
        if (agent != null) Destroy(agent.gameObject);
        isPlaying = false;
        Cursor.visible = true;
        Cursor.lockState = CursorLockMode.None;
    }

    void QuitGame() {
        if (currentPlayer != null && userControl) {
            currentPlayer.wallet.totalCoins += totalCollectedGame;
            currentPlayer.stats.totalTrapsHit += trapsHitCount;
            currentPlayer.stats.totalWins += winsCount;
            currentPlayer.currentCampaignLevel = Mathf.Max(currentPlayer.currentCampaignLevel, currentLevelIndex + 1);
            currentPlayer.Save(Path.Combine(Application.dataPath, "..", "player_save.json"));
        }

        // Se o jogo acabou e a campanha não foi concluída, foi porque bateu num gargalo (Game Over)
        if (!globalMetrics.campaign_completed) {
            globalMetrics.bottleneck_level = currentLevel != null ? currentLevel.level_id : 1;

            // Adiciona o relatório do nível onde falhou
            globalMetrics.level_reports.Add(new LevelReport {
                level_id = globalMetrics.bottleneck_level,
                mode = this.currentMode,
                total_rounds = currentLevelAttempts,
                wins = 0,
                win_rate = 0f, // 0 vitórias
                avg_time_to_goal = currentLevelAttempts > 0 ? (totalPlayTime / currentLevelAttempts) : 0f,
                stuck_events = stuckCount
            });
        }

        globalMetrics.is_human = userControl;

        // GRAVA O MEGA RELATÓRIO NO METRICS.JSON
        File.WriteAllText(Path.Combine(Application.dataPath, "..", "metrics.json"), JsonUtility.ToJson(globalMetrics, true));

        #if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
        #else
            Application.Quit();
        #endif
    }
}