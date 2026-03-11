using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using UnityEngine.Events;

public class UIManager : MonoBehaviour {
    public static UIManager Instance { get; private set; }
    private GameObject canvasGO;
    private GameObject currentMenu;
    private Font defaultFont;

    public enum UIState { None, Title, Vault, HUD, EndScreen, Pause }
    public UIState currentState = UIState.None;

    private Text timerText;
    private Text scoreText;
    private Text classText;
    private Text levelText;
    private Text livesText;

    void Awake() {
        if (Instance == null) Instance = this;
        defaultFont = Resources.GetBuiltinResource<Font>("Arial.ttf");
        if (defaultFont == null) defaultFont = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        SetupCanvas();
        SetupEventSystem();
    }

    void Start() {
        if (Application.isBatchMode || GameManager.Instance.isTrailerMode) {
            GameManager.Instance.StartNewRun();
        } else {
            ShowTitleScreen();
        }
    }

    void Update() {
        if (currentState == UIState.HUD && GameManager.Instance != null && !GameManager.Instance.finished)
        {
            if (timerText != null) {
                float timeLeft = GameManager.Instance.currentTimer;
                timerText.text = $"Tempo: {timeLeft:F1}s";

                // 🚨 PRESSÃO: Fica vermelho e avisa-te quando faltam menos de 10 segundos!
                if (timeLeft <= 10f) timerText.color = Color.red;
                else timerText.color = Color.white;
            }
            if (scoreText != null) {
                scoreText.text = $"Moedas: {GameManager.Instance.collectedInRound} / {GameManager.Instance.collectibles}";
            }
            if (levelText != null && GameManager.Instance.currentLevel != null) {
                levelText.text = $"NÍVEL {GameManager.Instance.currentLevel.level_id}";
            }
        }
    }

    public void HideUIForTrailer() {
        if (canvasGO != null) {
            canvasGO.SetActive(false);
        }
    }

    // ==========================================
    // MAGIA DO RATO E MENUS
    // ==========================================
    void UnlockMouse() {
        Cursor.visible = true;
        Cursor.lockState = CursorLockMode.None;
    }

    void ClearCurrentMenu() {
        if (currentMenu != null) Destroy(currentMenu);
    }

    public void ShowGlossary()
    {
        ClearCurrentMenu();
        currentState = UIState.Pause; // Mantém o estado de pausa para bloquear o jogo atrás
        currentMenu = CreatePanel("GlossaryMenu", new Color(0, 0, 0, 0.9f));

        // Título Central
        CreateText(currentMenu.transform, "MANUAL DE SOBREVIVÊNCIA", 65, new Vector2(0, 350), Color.yellow);

        // --- CATEGORIA: OBJETIVOS ---
        CreateText(currentMenu.transform, "OBJETIVOS", 40, new Vector2(-400, 200), Color.cyan);
        CreateText(currentMenu.transform, "💠 META: Alcança o portal para vencer o nível.", 28, new Vector2(-400, 140), Color.white);
        CreateText(currentMenu.transform, "💰 MOEDAS: Recolhe para comprar Vidas e Classes no Cofre.", 28, new Vector2(-400, 90), Color.white);

        // --- CATEGORIA: POWER-UPS ---
        CreateText(currentMenu.transform, "MELHORIAS (Power-Ups)", 40, new Vector2(-400, -50), Color.magenta);
        CreateText(currentMenu.transform, "🔵 BATERIA: Concede +5 segundos de tempo extra.", 28, new Vector2(-400, -110), Color.white);
        CreateText(currentMenu.transform, "🟣 RAIO: Aumenta a velocidade de movimento temporariamente.", 28, new Vector2(-400, -160), Color.white);

        // --- CATEGORIA: PERIGOS ---
        CreateText(currentMenu.transform, "PERIGOS", 40, new Vector2(300, 200), Color.red);
        CreateText(currentMenu.transform, "⚠️ ARMADILHA: Reduz o tempo restante ao pisar.", 28, new Vector2(300, 140), Color.white);
        CreateText(currentMenu.transform, "👾 INIMIGO: Perseguidores letais. Foge deles!", 28, new Vector2(300, 90), Color.white);

        // Dica de Gameplay
        CreateText(currentMenu.transform, "Dica: O Ninja tem maior velocidade mas visão limitada.", 24, new Vector2(0, -300), Color.gray);

        // Botão para Voltar ao Menu de Pausa
        CreateButton(currentMenu.transform, "VOLTAR", new Vector2(0, -400), new Vector2(250, 60), () => {
            ShowPauseMenu();
        });
    }

    public void ShowPauseMenu()
    {
        ClearCurrentMenu();
        currentState = UIState.Pause;
        UnlockMouse();
        currentMenu = CreatePanel("PauseMenu", new Color(0, 0, 0, 0.6f));

        CreateText(currentMenu.transform, "JOGO PAUSADO", 60, new Vector2(0, 150), Color.white);

        CreateButton(currentMenu.transform, "CONTINUAR", new Vector2(0, 20), new Vector2(300, 60), () => {
            GameManager.Instance.TogglePause();
        });
        CreateButton(currentMenu.transform, "GLOSSÁRIO", new Vector2(0, -30), new Vector2(300, 60), () => {
            ShowGlossary();
        });

        CreateButton(currentMenu.transform, "MENU PRINCIPAL", new Vector2(0, -70), new Vector2(300, 60), () => {
            GameManager.Instance.TogglePause(); // Tira a pausa antes de sair
            GameManager.Instance.UI_ReturnToMenu();
        });
    }

    // ==========================================
    // ECRÃS
    // ==========================================
    public void ShowTitleScreen() {
        ClearCurrentMenu();
        UnlockMouse();
        currentState = UIState.Title;
        currentMenu = CreatePanel("TitleScreen", new Color(0.1f, 0.1f, 0.15f, 1f));
        int moedas = GameManager.Instance.currentPlayer != null ? GameManager.Instance.currentPlayer.wallet.totalCoins : 0;
        int cristais = GameManager.Instance.currentPlayer != null ? GameManager.Instance.currentPlayer.wallet.timeCrystals : 0;
        int nivelAtual = GameManager.Instance.currentPlayer != null ? GameManager.Instance.currentPlayer.currentCampaignLevel : 1;

        CreateText(currentMenu.transform, "STUDIO-AI: A SIMULAÇÃO", 80, new Vector2(0, 250), Color.cyan);
        CreateText(currentMenu.transform, $"Nível {nivelAtual} | Moedas: {moedas} | Cristais de Tempo: {cristais} 💠", 35, new Vector2(0, 120), Color.yellow);
        CreateButton(currentMenu.transform, "INICIAR SIMULAÇÃO", new Vector2(0, -50), new Vector2(300, 60), () => {
            ShowHUD();
            GameManager.Instance.StartNewRun();
        });
        CreateButton(currentMenu.transform, "O COFRE (Classes)", new Vector2(0, -130), new Vector2(300, 60), () => {
            ShowVaultScreen();
        });
        CreateButton(currentMenu.transform, "RECOMECAR TUDO", new Vector2(0, -130), new Vector2(300, 60), () => {
            GameManager.Instance.ResetTotalProgress();
        });
        CreateButton(currentMenu.transform, "SAIR", new Vector2(0, -210), new Vector2(300, 60), () => {
            Application.Quit();
        });
    }

    public void ShowVaultScreen() {
        ClearCurrentMenu();
        UnlockMouse();
        currentState = UIState.Title;
        currentMenu = CreatePanel("VaultScreen", new Color(0.1f, 0.15f, 0.2f, 1f)); // Fundo azul escuro/néon

        int moedas = GameManager.Instance.currentPlayer != null ? GameManager.Instance.currentPlayer.wallet.totalCoins : 0;
        int cristais = GameManager.Instance.currentPlayer != null ? GameManager.Instance.currentPlayer.wallet.timeCrystals : 0;
        int vidasMaximas = GameManager.Instance.currentPlayer != null ? GameManager.Instance.currentPlayer.stats.maxLives : 3;

        // 🛡️ Segurança para a lista de classes do Save
        if (GameManager.Instance.currentPlayer != null && GameManager.Instance.currentPlayer.unlockedClasses == null) {
            GameManager.Instance.currentPlayer.unlockedClasses = new System.Collections.Generic.List<string> { "Explorer" };
        }

        CreateText(currentMenu.transform, "O COFRE", 60, new Vector2(0, 420), Color.yellow);
        CreateText(currentMenu.transform, $"Moedas: {moedas}  |  Cristais: {cristais} 💠  |  Vidas Máx: {vidasMaximas}", 30, new Vector2(0, 350), Color.cyan);

        // ==========================================
        // GRELHA VISUAL (UPGRADES + CLASSES)
        // ==========================================
        float startX = -250f;
        float startY = 100f;  // Subimos um pouco para caber 2 linhas sem bater no "Voltar"
        float espacamentoX = 500f;
        float espacamentoY = -400f;
        int colunas = 2;
        int contador = 0;

        // ------------------------------------------
        // CARTA 1: VIDA EXTRA
        // ------------------------------------------
        int l_vida = contador / colunas;
        int c_vida = contador % colunas;
        float posX_vida = startX + (c_vida * espacamentoX);
        float posY_vida = startY + (l_vida * espacamentoY);

        GameObject cardVida = new GameObject("Card_Vida");
        cardVida.transform.SetParent(currentMenu.transform, false);
        Image bgVida = cardVida.AddComponent<Image>();
        bgVida.color = new Color(0.15f, 0.1f, 0.1f, 0.9f); // Fundo ligeiramente avermelhado
        RectTransform rectVida = cardVida.GetComponent<RectTransform>();
        rectVida.anchoredPosition = new Vector2(posX_vida, posY_vida);
        rectVida.sizeDelta = new Vector2(350, 380);

        CreateText(cardVida.transform, "Vida Extra", 35, new Vector2(0, 150), Color.white);

        // Em vez de Imagem, usamos um Coração Gigante Textual
        CreateText(cardVida.transform, "❤️", 120, new Vector2(0, 30), Color.white);

        Button btnVida = CreateButton(cardVida.transform, "COMPRAR (50 M)", new Vector2(0, -130), new Vector2(300, 60), () => {
            if (GameManager.Instance.currentPlayer.wallet.totalCoins >= 50) { // 🚨 Corrigido para 50!
                GameManager.Instance.currentPlayer.wallet.totalCoins -= 50;
                GameManager.Instance.currentPlayer.stats.maxLives++;
                GameManager.Instance.currentPlayer.stats.currentLives++;
                GameManager.Instance.currentPlayer.Save(System.IO.Path.Combine(Application.dataPath, "..", "player_save.json"));
                ShowVaultScreen();
            } else {
                Debug.Log("Dinheiro insuficiente!");
            }
        });

        // Fica vermelho se não houver dinheiro
        if (moedas < 50) btnVida.GetComponent<Image>().color = new Color(0.6f, 0.2f, 0.2f, 1f);

        contador++; // Avançamos um espaço na grelha!

        // ------------------------------------------
        // CARTAS 2+: CLASSES DE PERSONAGENS
        // ------------------------------------------
        if (GameManager.Instance.roster != null && GameManager.Instance.roster.classes != null) {
            foreach (var c in GameManager.Instance.roster.classes) {
                bool isUnlocked = GameManager.Instance.currentPlayer.unlockedClasses.Contains(c.id);
                bool isEquipped = GameManager.Instance.currentPlayer.loadout.selectedClassID == c.id;

                int linha = contador / colunas;
                int coluna = contador % colunas;
                float posX = startX + (coluna * espacamentoX);
                float posY = startY + (linha * espacamentoY);

                GameObject cardGO = new GameObject("Card_" + c.name);
                cardGO.transform.SetParent(currentMenu.transform, false);
                Image cardBg = cardGO.AddComponent<Image>();
                cardBg.color = isEquipped ? new Color(0.2f, 0.5f, 0.2f, 0.8f) : new Color(0.1f, 0.1f, 0.1f, 0.8f);
                RectTransform cardRect = cardGO.GetComponent<RectTransform>();
                cardRect.anchoredPosition = new Vector2(posX, posY);
                cardRect.sizeDelta = new Vector2(350, 380); // Ajustado para ficar igual à Vida

                GameObject iconGO = new GameObject("Icon");
                iconGO.transform.SetParent(cardGO.transform, false);
                RawImage img = iconGO.AddComponent<RawImage>();

                Texture2D tex = Resources.Load<Texture2D>("Sprites/" + c.spriteName);
                if (tex == null) tex = Resources.Load<Texture2D>("Sprites/PlayerSprite");
                if (tex != null) img.texture = tex;

                RectTransform iconRect = iconGO.GetComponent<RectTransform>();
                iconRect.anchoredPosition = new Vector2(0, 30); // Fica centrado no peito da carta
                iconRect.sizeDelta = new Vector2(200, 200);

                CreateText(cardGO.transform, c.name, 35, new Vector2(0, 150), Color.white).GetComponent<RectTransform>().sizeDelta = new Vector2(330, 50);

                string btnText = "";
                UnityEngine.Events.UnityAction action = null;

                if (isEquipped) {
                    btnText = "✔️ EQUIPADO";
                    action = () => { Debug.Log("Já está equipado!"); };
                } else if (isUnlocked) {
                    btnText = "EQUIPAR";
                    action = () => {
                        GameManager.Instance.SetSelectedClass(c);
                        ShowVaultScreen();
                    };
                } else {
                    btnText = $"COMPRAR ({c.cost} M)";
                    action = () => {
                        if (GameManager.Instance.currentPlayer.wallet.totalCoins >= c.cost) {
                            GameManager.Instance.currentPlayer.wallet.totalCoins -= c.cost;
                            GameManager.Instance.currentPlayer.unlockedClasses.Add(c.id);
                            GameManager.Instance.SetSelectedClass(c);
                            GameManager.Instance.currentPlayer.Save(System.IO.Path.Combine(Application.dataPath, "..", "player_save.json"));
                            ShowVaultScreen();
                        }
                    };
                }

                Button actionBtn = CreateButton(cardGO.transform, btnText, new Vector2(0, -130), new Vector2(300, 60), action);

                if (!isUnlocked && GameManager.Instance.currentPlayer.wallet.totalCoins < c.cost) {
                    actionBtn.GetComponent<Image>().color = new Color(0.6f, 0.2f, 0.2f, 1f);
                }
                contador++;
            }
        }

        // 3. BOTÃO DE VOLTAR (No fundo ao centro, flutuante)
        CreateButton(currentMenu.transform, "VOLTAR AO MENU", new Vector2(0, -470), new Vector2(300, 60), () => {
            ShowTitleScreen();
        });
    }

    public void ShowHUD() {
       ClearCurrentMenu();
       currentState = UIState.HUD;
       // Criamos um painel que ocupa o ecrã todo mas é invisível
       currentMenu = CreatePanel("HUD_Root", new Color(0, 0, 0, 0));

       // 1. Criar Contentor do Timer (Topo Esquerdo)
       timerText = CreateText(currentMenu.transform, "Tempo: --", 40, new Vector2(100, -50), Color.white);
       RectTransform timerRect = timerText.GetComponent<RectTransform>();
       timerRect.anchorMin = new Vector2(0, 1);
       timerRect.anchorMax = new Vector2(0, 1);
       timerRect.pivot = new Vector2(0, 1);
       timerText.alignment = TextAnchor.UpperLeft;

       // 2. Criar Contentor das Moedas (Topo Direito)
       scoreText = CreateText(currentMenu.transform, "Moedas: --", 40, new Vector2(-100, -50), Color.yellow);
       RectTransform scoreRect = scoreText.GetComponent<RectTransform>();
       scoreRect.anchorMin = new Vector2(1, 1);
       scoreRect.anchorMax = new Vector2(1, 1);
       scoreRect.pivot = new Vector2(1, 1);
       scoreText.alignment = TextAnchor.UpperRight;

       // 3. Criar Info da Classe (Fundo Esquerdo)
       string className = GameManager.Instance.selectedClass != null ? GameManager.Instance.selectedClass.name : "Desconhecido";
       classText = CreateText(currentMenu.transform, $"Classe: {className}", 30, new Vector2(100, 50), Color.cyan);
       RectTransform classRect = classText.GetComponent<RectTransform>();
       classRect.anchorMin = new Vector2(0, 0);
       classRect.anchorMax = new Vector2(0, 0);
       classRect.pivot = new Vector2(0, 0);
       classText.alignment = TextAnchor.LowerLeft;

        // 4. Criar Info do Nível (Topo Centro)
        levelText = CreateText(currentMenu.transform, "NÍVEL --", 50, new Vector2(0, -50), Color.cyan);
        RectTransform levelRect = levelText.GetComponent<RectTransform>();
        levelRect.anchorMin = new Vector2(0.5f, 1);
        levelRect.anchorMax = new Vector2(0.5f, 1);
        levelRect.pivot = new Vector2(0.5f, 1);
        levelText.alignment = TextAnchor.UpperCenter;

        string initialLives = "--";
        if (GameManager.Instance != null && GameManager.Instance.currentPlayer != null) {
            initialLives = GameManager.Instance.currentPlayer.stats.currentLives.ToString();
        }
        livesText = CreateText(currentMenu.transform, $"❤️ Vidas: {initialLives}", 40, new Vector2(-100, 50), Color.red);
        RectTransform livesRect = livesText.GetComponent<RectTransform>();
        livesRect.anchorMin = new Vector2(1, 0); // Fica preso ao Canto Inferior Direito
        livesRect.anchorMax = new Vector2(1, 0);
        livesRect.pivot = new Vector2(1, 0);
        livesText.alignment = TextAnchor.LowerRight;
    }

    public void ShowEndScreen(bool victory, string reason) {
        ClearCurrentMenu();
        UnlockMouse(); // DEVOLVE O RATO!
        currentState = UIState.EndScreen;
        currentMenu = CreatePanel("EndScreen", new Color(0, 0, 0, 0.8f));

        Color titleColor = victory ? Color.green : Color.red;
        string titleText = victory ? "SOBREVIVESTE" : "SISTEMA FALHOU";

        CreateText(currentMenu.transform, titleText, 80, new Vector2(0, 100), titleColor);
        CreateText(currentMenu.transform, reason, 40, new Vector2(0, 0), Color.white);

        // Se o jogador chegou ao fim de tudo (Nível 10), não faz sentido o botão de próximo nível
        bool campaignOver = GameManager.Instance.globalMetrics.campaign_completed;

        if (victory && !campaignOver)
        {
            // BOTÃO 1: PRÓXIMO NÍVEL (Se ganhou e ainda há níveis)
            CreateButton(currentMenu.transform, "PRÓXIMO NÍVEL", new Vector2(-180, -150), new Vector2(300, 60), () => {
                GameManager.Instance.UI_PlayNextLevel();
            });

            // BOTÃO 2: VOLTAR AO MENU (Lado direito)
            CreateButton(currentMenu.transform, "VOLTAR AO MENU", new Vector2(180, -150), new Vector2(300, 60), () => {
                GameManager.Instance.UI_ReturnToMenu();
            });
        }
        else
        {
            // Se perdeu (Game Over) OU Se Ganhou a Campanha Inteira (só precisa do botão de Menu)
            CreateButton(currentMenu.transform, "VOLTAR AO MENU", new Vector2(0, -150), new Vector2(300, 60), () => {
                GameManager.Instance.UI_ReturnToMenu();
            });
        }
    }

    // ==========================================
    // FÁBRICA DE UI
    // ==========================================
    void SetupCanvas() {
        canvasGO = new GameObject("MasterCanvas");
        Canvas canvas = canvasGO.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        CanvasScaler scaler = canvasGO.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);
        canvasGO.AddComponent<GraphicRaycaster>();
    }

    void SetupEventSystem() {
        if (Object.FindFirstObjectByType<EventSystem>() == null) {
            GameObject eventSystemGO = new GameObject("EventSystem");
            eventSystemGO.AddComponent<EventSystem>();
            eventSystemGO.AddComponent<StandaloneInputModule>();
        }
    }

    GameObject CreatePanel(string name, Color color) {
        GameObject panel = new GameObject(name);
        panel.transform.SetParent(canvasGO.transform, false);
        Image img = panel.AddComponent<Image>();
        img.color = color;
        RectTransform rect = panel.GetComponent<RectTransform>();
        rect.anchorMin = Vector2.zero;
        rect.anchorMax = Vector2.one;
        rect.sizeDelta = Vector2.zero;
        return panel;
    }

    Text CreateText(Transform parent, string content, int fontSize, Vector2 position, Color color) {
        GameObject txtGO = new GameObject("Text");
        txtGO.transform.SetParent(parent, false);
        Text txt = txtGO.AddComponent<Text>();
        txt.font = defaultFont;
        txt.text = content;
        txt.fontSize = fontSize;
        txt.alignment = TextAnchor.MiddleCenter;
        txt.color = color;

        // Impede que o texto seja cortado!
        txt.horizontalOverflow = HorizontalWrapMode.Overflow;
        txt.verticalOverflow = VerticalWrapMode.Overflow;

        RectTransform rect = txtGO.GetComponent<RectTransform>();
        rect.anchoredPosition = position;
        rect.sizeDelta = new Vector2(1200, 150);
        return txt;
    }

    Button CreateButton(Transform parent, string text, Vector2 position, Vector2 size, UnityAction onClick) {
        GameObject btnGO = new GameObject("Button");
        btnGO.transform.SetParent(parent, false);
        Image img = btnGO.AddComponent<Image>();
        img.color = new Color(0.2f, 0.2f, 0.2f, 1f);
        Button btn = btnGO.AddComponent<Button>();
        btn.onClick.AddListener(onClick);

        RectTransform rect = btnGO.GetComponent<RectTransform>();
        rect.anchoredPosition = position;
        rect.sizeDelta = size;

        Text btnText = CreateText(btnGO.transform, text, 24, Vector2.zero, Color.white);
        btnText.GetComponent<RectTransform>().sizeDelta = size;

        return btn;
    }
}