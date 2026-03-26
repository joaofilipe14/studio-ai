using UnityEngine;
using System.Collections.Generic;
using System.IO;

[System.Serializable]
public class LevelReport {
    public int level_id;
    public int total_rounds;
    public int wins;
    public float win_rate;
    public float time_to_win;
    public int lives_lost;
    public int timeouts;
    public int collected_coins;
    public int collected_crystals;
    public int powerups_used;
}

[System.Serializable]
public class ItemPurchase {
    public string itemID;
    public int quantity;
}

[System.Serializable]
public class CampaignMetrics {
    public bool campaign_completed; // Chegou ao fim do nível 10?
    public int bottleneck_level;
    public bool is_human;
    public List<LevelReport> level_reports = new List<LevelReport>();
}

public class GameManager : MonoBehaviour {
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
    public SafeRoomCatalog safeRoomCatalog { get; private set; }
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
    public int collectedInRound = 0;

    [Header("Agente e Inimigo")]
    public float agentMoveSpeed = 4.5f;
    public bool userControl = true;
    public float chaserMoveSpeed = 3.5f;

    [Header("Buffs Ativos da Run (Safe Room)")]
    public List<ItemPurchase> tempPurchasedItems = new List<ItemPurchase>();
    public float currentRunSpeedMultiplier = 1f;
    public float currentRunTrapMultiplier = 1f;
    public float currentRunVisionBonus = 0f;
    [Header("Power-ups")]
    public float timeBoostAmount = 5f;
    public float speedBoostMultiplier = 1.5f;
    public float speedBoostDuration = 3f;

    [Header("Métricas Internas")]
    private int winsCount = 0;
    private int timeoutsCount = 0;
    private int livesLostCount = 0;
    public int powerupsUsedCount = 0;
    public int trapsHitCount = 0;
    private int totalCollectedGame = 0;
    private float totalPlayTime = 0f;
    private float roundPlayTime = 0f;

    [Header("Marketing & Media")]
    public TrailerDirector trailerDirector;
    public bool isTrailerMode = false;
    public string trailerFolderPath = "";

    [Header("Relatório Global")]
    public CampaignMetrics globalMetrics = new CampaignMetrics();

    [Header("Referências")]
    public GridWorld world;
    public SimpleAgent agent;

    [Header("Regras da Campanha")]
    public int currentLevelAttempts = 0;

    [Header("Áudio e SFX")]
    private AudioSource sfxSource;

    void Awake() {
        if (Instance == null) Instance = this;
        RenderSettings.skybox = null;
        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.15f, 0.15f, 0.2f);
        string[] args = System.Environment.GetCommandLineArgs();
        for (int i = 0; i < args.Length; i++) {
            if (args[i] == "-trailerMode") isTrailerMode = true;
            if (args[i] == "-botMode") userControl = false;
            if (args[i] == "-trailerFolder" && i + 1 < args.Length) {
                trailerFolderPath = args[i + 1];
            }
        }
        if (gameObject.GetComponent<UIManager>() == null) gameObject.AddComponent<UIManager>();
        SetupGlobalLight();
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
        collectibles = currentLevel.rules.targetCount;
        chaserMoveSpeed = currentLevel.rules.enemySpeed;
        gridWidth = (int)(currentLevel.arena.halfSize * 2);
        gridHeight = (int)(currentLevel.arena.halfSize * 2);
        seed = currentLevel.seed;
        timeLimit = currentLevel.rules.timeLimit;
        if (timeLimit <= 0.1f) timeLimit = 30f;
        if (currentPlayer.purchasedUpgrades != null) {
            timeLimit += (currentPlayer.purchasedUpgrades.startExtraTimeLvl * 10f);
        }
        currentTimer = timeLimit;
        if (currentLevelAttempts <= 1) {
            currentActiveSeed = seed;
        } else {
            currentActiveSeed = seed + UnityEngine.Random.Range(1000, 99999);
        }
        Debug.Log($"A iniciar Nível {currentLevel.level_id} | Semente Ativa: {currentActiveSeed} | Obstáculos: {currentLevel.obstacles.count}");
        if (!Application.isBatchMode && GameObject.Find("BackgroundMusic") == null) SetupAudio();
        if (world == null) world = gameObject.AddComponent<GridWorld>();
        world.Build(gridWidth, gridHeight, cellSize, currentLevel.obstacles.count, currentActiveSeed);
        CleanupScene();
        BuildFloorAndObstacles();
        System.Random rng = new System.Random(currentActiveSeed);
        LevelSpawner.ResetSpawns();
        float permSpeedBonus = (currentPlayer.purchasedUpgrades != null) ? (currentPlayer.purchasedUpgrades.permSpeedLvl * 0.5f) : 0f;
        agentMoveSpeed = (selectedClass.stats.speed + permSpeedBonus) * currentRunSpeedMultiplier;
        float vRadius = selectedClass != null ? selectedClass.stats.visionRadius : 8.0f;
        vRadius += currentRunVisionBonus;
        string spriteToLoad = selectedClass != null ? selectedClass.spriteName : "PlayerSprite";
        if (agent == null) {
            agent = LevelSpawner.SpawnAgent(world, rng, agentMoveSpeed, userControl, vRadius, spriteToLoad);
        } else {
            Vector2Int newStart = LevelSpawner.GetUniqueSpawnPosition(world, rng);
            agent.world = world;
            agent.moveSpeed = agentMoveSpeed;
            agent.ResetPosition(newStart);
            Light agentLight = agent.GetComponentInChildren<Light>();
            if (agentLight != null) agentLight.range = vRadius;
        }
        LevelSpawner.CalculateReachableArea(world, agent.gridPos);

        float minGoalDistance = Mathf.Max(gridWidth, gridHeight) * 0.4f;
        float minEnemySafeDistance = Mathf.Max(gridWidth, gridHeight) * 0.3f;

        if (currentLevel.rules.enemyCount > 0)
            LevelSpawner.SpawnEnemies(world, rng, currentLevel.rules.enemyCount, chaserMoveSpeed, agent.gridPos, minEnemySafeDistance);

        LevelSpawner.SpawnGoal(world, rng, agent.gridPos, minGoalDistance);

        if (collectibles > 0)
            LevelSpawner.SpawnCollectibles(world, rng, collectibles);

        int powerUpsToSpawn = currentPlayer.stats.basePowerUpCount;
        if (currentPlayer.purchasedUpgrades != null) {
            powerUpsToSpawn += currentPlayer.purchasedUpgrades.morePowerUpsLvl;
        }
        if (powerUpsToSpawn > 0)
            LevelSpawner.SpawnPowerUps(world, rng, powerUpsToSpawn);

        int baseTraps = currentLevel.rules.trapCount;
        float permTrapReduction = (currentPlayer.purchasedUpgrades != null) ? (currentPlayer.purchasedUpgrades.trapReductionLvl * 0.05f) : 0f;
        float finalTrapMultiplier = Mathf.Clamp01((1f - permTrapReduction) * currentRunTrapMultiplier);
        int finalTraps = Mathf.RoundToInt(baseTraps * finalTrapMultiplier);

        if (finalTraps > 0)
            LevelSpawner.SpawnTraps(world, rng, finalTraps, currentLevel.rules.trapPenalty);
        if (currentLevel.level_id == 1 && !currentPlayer.stats.hasSeenTutorial && userControl) {
            Debug.Log($"TutorialManager");
            TutorialManager.ShowTutorial();
            currentPlayer.stats.hasSeenTutorial = true;
            string savePath = System.IO.Path.Combine(Application.dataPath, "..", "player_save.json");
            currentPlayer.Save(savePath);
        } else {
            Debug.Log($"!TutorialManager");
            if (userControl) {
                UIManager.Instance.ShowHUD();
                Cursor.visible = false;
                Cursor.lockState = CursorLockMode.Locked;
            }
        }
        if (isTrailerMode) {
            if (UIManager.Instance != null) UIManager.Instance.HideUIForTrailer();

            if (trailerDirector == null) trailerDirector = gameObject.AddComponent<TrailerDirector>();
            Vector3 heroTarget = (agent != null) ? agent.transform.position : new Vector3((gridWidth * cellSize) / 2f, 0, (gridHeight * cellSize) / 2f);
            trailerDirector.StartHeroShot(heroTarget, trailerFolderPath, () => {
                #if UNITY_EDITOR
                    UnityEditor.EditorApplication.isPlaying = false;
                #else
                    Application.Quit();
                #endif
            });
            return;
        }
    }

    void SetupGlobalLight() {
        Light[] allLights = Object.FindObjectsByType<Light>(FindObjectsSortMode.None);
        bool hasSun = false;
        foreach (Light l in allLights) {
            if (l.type == LightType.Directional) hasSun = true;
        }
        if (!hasSun) {
            GameObject lightObj = new GameObject("GlobalSun");
            Light sun = lightObj.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(0.3f, 0.4f, 0.6f); // Azul claro Cyberpunk
            sun.intensity = 2.9f; // Força da luz global
            lightObj.transform.rotation = Quaternion.Euler(50, -30, 0);
        }
    }

    public void ResetTotalProgress() {
        string savePath = Path.Combine(Application.dataPath, "..", "player_save.json");
        if (File.Exists(savePath)) {
            File.Delete(savePath); // Apaga o ficheiro físico
            Debug.Log("Ficheiro de Save apagado. Reiniciando progresso...");
        }
        LoadGenomeConfig();
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
        Texture2D tex = Resources.Load<Texture2D>("Textures/" + textureName);

        Shader standardShader = Shader.Find("Standard");
        if (standardShader == null) standardShader = Shader.Find("Legacy Shaders/VertexLit");
        Material mat = new Material(standardShader);

        if (tex != null) {
            mat.color = Color.white;
            mat.mainTexture = tex;

            if (textureName == "FloorTexture") {
                mat.mainTextureScale = new Vector2(gridWidth / 4f, gridHeight / 4f);
                mat.SetFloat("_Glossiness", 0.7f); // Chão reflexivo
            } else {
                mat.SetFloat("_Glossiness", 0.3f); // Paredes baças, reagem à luz do jogador
            }
        } else {
            // Fallback apenas se a textura não existir
            if (textureName == "FloorTexture") ColorUtility.TryParseHtmlString("#151515", out fallbackColor);
            else if (textureName == "ObstacleTexture") ColorUtility.TryParseHtmlString("#0A151A", out fallbackColor);

            mat.color = fallbackColor;
            mat.SetFloat("_Glossiness", 0.5f);
        }

        return mat; // Removemos completamente as Emissões forçadas por código!
    }

    void LoadGenomeConfig() {
        // LÊ A CAMPANHA INTEIRA E OS NOVOS FICHEIROS
        string campaignPath = Path.Combine(Application.dataPath, "..", "level_genome.json");
        string rosterPath = Path.Combine(Application.dataPath, "..", "roster.json");
        string savePath = Path.Combine(Application.dataPath, "..", "player_save.json");
        string safeRoomPath = Path.Combine(Application.dataPath, "..", "safe_room_items.json");

        roster = Roster.Load(rosterPath);
        currentPlayer = PlayerSave.Load(savePath);
        safeRoomCatalog = SafeRoomCatalog.Load(safeRoomPath);

        if (File.Exists(campaignPath)) {
            string json = File.ReadAllText(campaignPath);
            LevelGenome[] loadedLevels = JsonHelper.FromJson<LevelGenome>(json);
            if (loadedLevels != null && loadedLevels.Length > 0) {
                campaignData = new List<LevelGenome>(loadedLevels);
            }
        }
        if (roster != null && currentPlayer != null && currentPlayer.loadout != null)
            selectedClass = roster.classes.Find(c => c.id == currentPlayer.loadout.selectedClassID);
        if (currentPlayer != null && campaignData.Count > 0) {
            currentLevelIndex = Mathf.Clamp(currentPlayer.currentCampaignLevel - 1, 0, campaignData.Count - 1);
            Debug.Log($"[Save Loaded] A arrancar a Campanha no Index {currentLevelIndex} (Nível {currentPlayer.currentCampaignLevel})");
        }
    }

    void SetupAudio() {
        GameObject musicObj = GameObject.Find("BackgroundMusic") ?? new GameObject("BackgroundMusic");
        AudioSource musicSource = musicObj.GetComponent<AudioSource>() ?? musicObj.AddComponent<AudioSource>();
        musicSource.clip = Resources.Load<AudioClip>("Music/bg_theme"); // Nome atualizado para o novo sistema
        musicSource.loop = true;
        musicSource.volume = 0.4f;
        if (!musicSource.isPlaying) musicSource.Play();
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
            isPlaying = false;
            HandleDamage("TEMPO ESGOTADO");
        }
    }

    public void TogglePause() {
        isPaused = !isPaused;
        if (isPaused) {
            Time.timeScale = 0f;
            UIManager.Instance.ShowPauseMenu();
        } else {
            Debug.Log("!TogglePause");
            Time.timeScale = 1f;
            UIManager.Instance.ShowHUD();
            if (userControl) {
               // Cursor.visible = false;
                //Cursor.lockState = CursorLockMode.Locked;
            }
        }
    }

    public void HandleDamage(string reason) {
        if (finished) return;
        if (reason.Contains("Inimigo")) livesLostCount++;
        else if (reason.Contains("TEMPO")) timeoutsCount++;
        currentPlayer.stats.currentLives--;
        currentPlayer.Save(Path.Combine(Application.dataPath, "..", "player_save.json"));
        if (userControl) {
            if (Camera.main != null) {
                var cam = Camera.main.GetComponent<CameraController>();
                if (cam != null) cam.TriggerShake(0.5f, 0.6f);
            }
            PlaySFX("sfx_lose");
        }
        if (currentPlayer.stats.currentLives <= 0) {
            finished = true;
            isPlaying = false;
            currentRunSpeedMultiplier = 1f;
            currentRunVisionBonus = 0f;
            currentRunTrapMultiplier = 1f;
            tempPurchasedItems.Clear();
            int vidasCompradas = Mathf.Max(0, currentPlayer.stats.maxLives - 3);
            int vidaTotal = selectedClass.stats.baseLives + vidasCompradas;
            if (userControl) {
                LevelReport newReport = new LevelReport {
                    level_id = currentLevel.level_id,
                    total_rounds = currentLevelAttempts,
                    wins = 0,
                    win_rate = 0f,
                    time_to_win = 0f,
                    lives_lost = livesLostCount,
                    timeouts = timeoutsCount,
                    collected_coins = collectedInRound,
                    collected_crystals = 0,
                    powerups_used = powerupsUsedCount
                };
                Debug.Log($"[📊 METRICS REPORT] Nível {newReport.level_id} Concluído!\n" +
                          $"↳ Tentativas: {newReport.total_rounds} | Win Rate: {newReport.win_rate:F2}\n" +
                          $"↳ Tempo de Fuga: {newReport.time_to_win:F2}s | Timeouts: {newReport.timeouts}\n" +
                          $"↳ Vidas Perdidas: {newReport.lives_lost}\n" +
                          $"↳ Dinheiro: {newReport.collected_coins} Moedas | {newReport.collected_crystals} Cristais\n" +
                          $"↳ Powerups Usados: {newReport.powerups_used}");

                // 3. Adiciona o relatório guardado à lista global
                globalMetrics.level_reports.Add(newReport);
                SaveMetrics();

                currentPlayer.stats.currentLives = vidaTotal;
                currentPlayer.currentCampaignLevel = 1;
                currentPlayer.wallet.totalCoins = 0;
                collectedInRound = 0;
                currentPlayer.Save(Path.Combine(Application.dataPath, "..", "player_save.json"));

                if (UIManager.Instance != null)
                    UIManager.Instance.ShowEndScreen(false, $"GAME OVER no Nível {currentLevel.level_id}!\nFicaste sem vidas.\nMotivo: {reason}");
            } else {
                Debug.Log($"[BOT] Game Over no Nível {currentLevel.level_id}. A voltar ao Cofre para comprar Upgrades...");
                LevelReport newReport = new LevelReport {
                    level_id = currentLevel != null ? currentLevel.level_id : 1,
                    total_rounds = currentLevelAttempts,
                    wins = 0, win_rate = 0f, time_to_win = 0f,
                    lives_lost = livesLostCount, timeouts = timeoutsCount,
                    collected_coins = collectedInRound, collected_crystals = 0,
                    powerups_used = powerupsUsedCount
                };
                Debug.Log($"[📊 METRICS REPORT] Nível {newReport.level_id} Concluído!\n" +
                          $"↳ Tentativas: {newReport.total_rounds} | Win Rate: {newReport.win_rate:F2}\n" +
                          $"↳ Tempo de Fuga: {newReport.time_to_win:F2}s | Timeouts: {newReport.timeouts}\n" +
                          $"↳ Vidas Perdidas: {newReport.lives_lost}\n" +
                          $"↳ Dinheiro: {newReport.collected_coins} Moedas | {newReport.collected_crystals} Cristais\n" +
                          $"↳ Powerups Usados: {newReport.powerups_used}");

                globalMetrics.level_reports.Add(newReport);
                if (roster != null && roster.items != null) {
                    if (currentPlayer.purchasedUpgrades == null) currentPlayer.purchasedUpgrades = new PlayerUpgrades();
                    if (currentPlayer.purchasedItems == null) currentPlayer.purchasedItems = new System.Collections.Generic.List<ItemPurchase>();

                    foreach (var item in roster.items) {
                        // 1. O Bot verifica se já atingiu o limite máximo deste item!
                        bool isMaxedOut = false;
                        if (item.id == "item_life" && currentPlayer.stats.maxLives >= 7) isMaxedOut = true;
                        else if (item.id == "item_perm_speed" && currentPlayer.purchasedUpgrades.permSpeedLvl >= 5) isMaxedOut = true;
                        else if (item.id == "item_trap_reduction" && currentPlayer.purchasedUpgrades.trapReductionLvl >= 5) isMaxedOut = true;
                        else if (item.id == "item_time_boost" && currentPlayer.purchasedUpgrades.startExtraTimeLvl >= 5) isMaxedOut = true;

                        // 2. Se tiver dinheiro e não estiver no máximo, COMPRA!
                        if (!isMaxedOut && currentPlayer.wallet.timeCrystals >= item.cost) {
                            currentPlayer.wallet.timeCrystals -= item.cost;

                            // Aplica a melhoria real na física
                            if (item.id == "item_life") currentPlayer.stats.maxLives++;
                            else if (item.id == "item_time_boost") currentPlayer.purchasedUpgrades.startExtraTimeLvl++;
                            else if (item.id == "item_perm_speed") currentPlayer.purchasedUpgrades.permSpeedLvl++;
                            else if (item.id == "item_trap_reduction") currentPlayer.purchasedUpgrades.trapReductionLvl++;

                            // Regista a compra na lista visual (para sincronizar com UI e Saves)
                            var purchase = currentPlayer.purchasedItems.Find(p => p.itemID == item.id);
                            if (purchase != null) purchase.quantity++;
                            else currentPlayer.purchasedItems.Add(new ItemPurchase { itemID = item.id, quantity = 1 });

                            Debug.Log($"[BOT] Comprou Upgrade Permanente: {item.name} | Cristais Restantes: {currentPlayer.wallet.timeCrystals}");
                        }
                    }
                }
                vidaTotal = selectedClass.stats.baseLives + Mathf.Max(0, currentPlayer.stats.maxLives - 3);
                currentPlayer.stats.currentLives = vidaTotal;
                currentPlayer.currentCampaignLevel = 1;
                currentPlayer.wallet.totalCoins = 0;
                collectedInRound = 0;
                currentPlayer.Save(Path.Combine(Application.dataPath, "..", "player_save.json"));
                QuitGame();
            }
        }
    }

    public void OnGoalReached() {
        if (finished) return;
        //PlaySFX("sfx_win");
        finished = true;
        isPlaying = false;
        winsCount++;
        int timeCrystalsEarned = Mathf.FloorToInt(currentTimer);

        Debug.Log($"[ROUND STATS] Nível: {currentLevel.level_id} | Tentativa: {currentLevelAttempts} | Resultado: VITÓRIA | Tempo: {roundPlayTime:F1}s | Moedas: {collectedInRound}");

        LevelReport newReport = new LevelReport {
            level_id = currentLevel != null ? currentLevel.level_id : 1,
            total_rounds = currentLevelAttempts,
            wins = 1,
            win_rate = currentLevelAttempts > 0 ? 1f / currentLevelAttempts : 0f,
            time_to_win = roundPlayTime,
            lives_lost = livesLostCount,
            timeouts = timeoutsCount,
            collected_coins = collectedInRound,
            collected_crystals = timeCrystalsEarned,
            powerups_used = powerupsUsedCount
        };

        // 2. 🚨 O TEU LOG DE DETETIVE (Formato bonito na Consola)
        Debug.Log($"[📊 METRICS REPORT] Nível {newReport.level_id} Concluído!\n" +
                  $"↳ Tentativas: {newReport.total_rounds} | Win Rate: {newReport.win_rate:F2}\n" +
                  $"↳ Tempo de Fuga: {newReport.time_to_win:F2}s | Timeouts: {newReport.timeouts}\n" +
                  $"↳ Vidas Perdidas: {newReport.lives_lost}\n" +
                  $"↳ Dinheiro: {newReport.collected_coins} Moedas | {newReport.collected_crystals} Cristais\n" +
                  $"↳ Powerups Usados: {newReport.powerups_used}");

        // 3. Adiciona o relatório guardado à lista global
        globalMetrics.level_reports.Add(newReport);
        currentLevelIndex++;
        if (currentPlayer != null) {
            currentPlayer.wallet.totalCoins += collectedInRound;
            currentPlayer.wallet.timeCrystals += timeCrystalsEarned;
            currentPlayer.stats.totalWins++;
            currentPlayer.currentCampaignLevel++;
            currentPlayer.Save(System.IO.Path.Combine(Application.dataPath, "..", "player_save.json"));
            if (userControl) {
                SaveMetrics();
            }
        }

        currentLevelAttempts = 0;
        livesLostCount = 0;
        totalPlayTime = 0f;
        timeoutsCount = 0;

        if (currentLevelIndex >= campaignData.Count) {
            globalMetrics.campaign_completed = true; // 🎉 SUCESSO TOTAL!
            globalMetrics.bottleneck_level = 0;

            if (userControl) {
                SaveMetrics();
                if (UIManager.Instance != null) UIManager.Instance.ShowEndScreen(true, "CAMPANHA CONCLUÍDA! És uma Lenda!");
            }
            else QuitGame(); // O Bot completou a campanha, fecha o jogo para relatar ao Python!
        } else {
            if (userControl && UIManager.Instance != null) {
                if (currentLevel.level_id == 3 || currentLevel.level_id == 6 || currentLevel.level_id == 9) {
                    UIManager.Instance.ShowSafeRoomScreen();
                } else {
                    string rewardMsg = $"Nível Concluído!\n\nSobreviveste com {timeCrystalsEarned}s de sobra.\nConvertido em {timeCrystalsEarned} Cristais de Tempo 💠!";
                    UIManager.Instance.ShowEndScreen(true, rewardMsg);
                }
            } else {
                int completedLevelId = currentLevel != null ? currentLevel.level_id : 1;
                if (completedLevelId == 3 || completedLevelId == 6 || completedLevelId == 9) {
                    if (safeRoomCatalog != null && safeRoomCatalog.safeRoomItems != null) {
                        foreach (var item in safeRoomCatalog.safeRoomItems) {
                            if (currentPlayer.wallet.totalCoins >= item.cost) {
                                currentPlayer.wallet.totalCoins -= item.cost;
                                if (tempPurchasedItems == null) tempPurchasedItems = new System.Collections.Generic.List<ItemPurchase>();
                                var purchase = tempPurchasedItems.Find(p => p.itemID == item.id);
                                if (purchase != null) {
                                    purchase.quantity++;
                                } else {
                                    tempPurchasedItems.Add(new ItemPurchase { itemID = item.id, quantity = 1 });
                                }
                                if (item.effectType == "SpeedBoost") {
                                    currentRunSpeedMultiplier *= item.effectValue;
                                } else if (item.effectType == "VisionBoost") {
                                    currentRunVisionBonus += item.effectValue;
                                } else if (item.effectType == "TrapReduction") {
                                    currentRunTrapMultiplier *= item.effectValue;
                                }
                                Debug.Log($"[BOT] Entrou na Safe Room e comprou: {item.name}");
                                if (UIManager.Instance != null && UIManager.Instance.currentState == UIManager.UIState.HUD) {
                                    UIManager.Instance.RefreshActiveBuffsHUD();
                                }

                                break; // O Bot só compra 1 item e sai (mantive o teu break)
                            }
                        }
                    }
                }
                Invoke("StartNewRun", 0.05f);
            }
        }
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
            UIManager.Instance.ShowHUD();
        }
        StartNewRun();
    }

    public void UI_ReturnToMenu() {
        Time.timeScale = 1f;
        isPaused = false;
        currentLevelIndex = 0;
        currentLevelAttempts = 0;
        if (UIManager.Instance != null) {
            UIManager.Instance.ShowTitleScreen(); // Abre o Menu Principal
        }
        CleanupScene();
        CleanupScene();
        if (agent != null) Destroy(agent.gameObject);
        isPlaying = false;
        Cursor.visible = true;
        Cursor.lockState = CursorLockMode.None;
    }

    public void SaveMetrics() {
        globalMetrics.is_human = userControl;
        if (!globalMetrics.campaign_completed) {
            globalMetrics.bottleneck_level = currentLevel != null ? currentLevel.level_id : 1;
        }

        string path = Path.Combine(Application.dataPath, "..", "metrics.json");
        File.WriteAllText(path, JsonUtility.ToJson(globalMetrics, true));
        Debug.Log($"[METRICS] metrics.json guardado com sucesso em: {path}");
    }

    void QuitGame() {
        if (currentPlayer != null && userControl) {
            currentPlayer.stats.totalTrapsHit += trapsHitCount;
            currentPlayer.stats.totalWins += winsCount;
            currentPlayer.currentCampaignLevel = Mathf.Max(currentPlayer.currentCampaignLevel, currentLevelIndex + 1);
            currentPlayer.Save(Path.Combine(Application.dataPath, "..", "player_save.json"));
        }

        // Se o jogo acabou e a campanha não foi concluída, foi porque bateu num gargalo (Game Over)
        if (!globalMetrics.campaign_completed && !userControl) {
            globalMetrics.bottleneck_level = currentLevel != null ? currentLevel.level_id : 1;
        } else if (!userControl) {
            SaveMetrics();
        }
        File.WriteAllText(Path.Combine(Application.dataPath, "..", "metrics.json"), JsonUtility.ToJson(globalMetrics, true));

        #if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
        #else
            Application.Quit();
        #endif
    }
}