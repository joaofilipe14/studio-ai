using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using UnityEngine.Events;

public class UIManager : MonoBehaviour
{
    public static UIManager Instance { get; private set; }

    private GameObject canvasGO;
    private GameObject currentMenu;
    private Font defaultFont;

    public enum UIState { None, Title, Vault, HUD, EndScreen }
    public UIState currentState = UIState.None;

    private Text timerText;
    private Text scoreText;
    private Text classText;

    void Awake()
    {
        if (Instance == null) Instance = this;

        defaultFont = Resources.GetBuiltinResource<Font>("Arial.ttf");
        if (defaultFont == null) defaultFont = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

        SetupCanvas();
        SetupEventSystem();
    }

    void Start()
    {
        if (Application.isBatchMode) {
            GameManager.Instance.StartNewRun();
        } else {
            ShowTitleScreen();
        }
    }

    void Update()
    {
        if (currentState == UIState.HUD && GameManager.Instance != null && !GameManager.Instance.finished)
        {
            if (timerText != null) timerText.text = $"Tempo: {GameManager.Instance.timeLimit - GameManager.Instance.currentTimer:F1}s";

            if (scoreText != null) {
                if (GameManager.Instance.currentMode == "Collect")
                    scoreText.text = $"Moedas: {GameManager.Instance.collectedInRound} / {GameManager.Instance.collectibles}";
                else
                    scoreText.text = "Objetivo: Encontrar a Meta!";
            }
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

    // ==========================================
    // ECRÃS
    // ==========================================
    public void ShowTitleScreen()
    {
        ClearCurrentMenu();
        UnlockMouse(); // DEVOLVE O RATO!
        currentState = UIState.Title;
        currentMenu = CreatePanel("TitleScreen", new Color(0.1f, 0.1f, 0.15f, 1f));

        CreateText(currentMenu.transform, "STUDIO-AI: A SIMULAÇÃO", 80, new Vector2(0, 200), Color.cyan);
        CreateText(currentMenu.transform, "Seja bem-vindo, Humano.", 30, new Vector2(0, 100), Color.white);

        CreateButton(currentMenu.transform, "INICIAR SIMULAÇÃO", new Vector2(0, -50), new Vector2(300, 60), () => {
            ShowHUD();
            GameManager.Instance.StartNewRun();
        });

        CreateButton(currentMenu.transform, "O COFRE (Classes)", new Vector2(0, -130), new Vector2(300, 60), () => {
            ShowVaultScreen();
        });

        CreateButton(currentMenu.transform, "SAIR", new Vector2(0, -210), new Vector2(300, 60), () => {
            Application.Quit();
        });
    }

    public void ShowVaultScreen()
    {
        ClearCurrentMenu();
        UnlockMouse(); // DEVOLVE O RATO!
        currentState = UIState.Vault;
        currentMenu = CreatePanel("VaultScreen", new Color(0.15f, 0.1f, 0.1f, 1f));

        int coins = GameManager.Instance.currentPlayer != null ? GameManager.Instance.currentPlayer.wallet.totalCoins : 0;

        CreateText(currentMenu.transform, "O COFRE SECRETO", 60, new Vector2(0, 400), Color.yellow);
        CreateText(currentMenu.transform, $"Saldo Disponível: {coins} Moedas", 40, new Vector2(0, 320), Color.white);

        if (GameManager.Instance.roster != null && GameManager.Instance.roster.classes != null)
        {
            int offsetY = 150;
            foreach (var charClass in GameManager.Instance.roster.classes)
            {
                string info = $"{charClass.name} - Vel: {charClass.stats.speed} | Visão: {charClass.stats.visionRadius}";
                CreateText(currentMenu.transform, info, 30, new Vector2(-150, offsetY), Color.cyan);

                CreateButton(currentMenu.transform, "SELECIONAR", new Vector2(300, offsetY), new Vector2(200, 50), () => {
                    GameManager.Instance.SetSelectedClass(charClass);
                    ShowTitleScreen();
                });

                offsetY -= 80;
            }
        }

        CreateButton(currentMenu.transform, "VOLTAR", new Vector2(0, -400), new Vector2(250, 60), () => {
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
       timerRect.anchorMin = new Vector2(0, 1); // Canto Superior Esquerdo
       timerRect.anchorMax = new Vector2(0, 1);
       timerRect.pivot = new Vector2(0, 1);
       timerText.alignment = TextAnchor.UpperLeft;

       // 2. Criar Contentor das Moedas (Topo Direito)
       scoreText = CreateText(currentMenu.transform, "Moedas: --", 40, new Vector2(-100, -50), Color.yellow);
       RectTransform scoreRect = scoreText.GetComponent<RectTransform>();
       scoreRect.anchorMin = new Vector2(1, 1); // Canto Superior Direito
       scoreRect.anchorMax = new Vector2(1, 1);
       scoreRect.pivot = new Vector2(1, 1);
       scoreText.alignment = TextAnchor.UpperRight;

       // 3. Criar Info da Classe (Fundo Esquerdo)
       string className = GameManager.Instance.selectedClass != null ? GameManager.Instance.selectedClass.name : "Desconhecido";
       classText = CreateText(currentMenu.transform, $"Classe: {className}", 30, new Vector2(100, 50), Color.cyan);
       RectTransform classRect = classText.GetComponent<RectTransform>();
       classRect.anchorMin = new Vector2(0, 0); // Canto Inferior Esquerdo
       classRect.anchorMax = new Vector2(0, 0);
       classRect.pivot = new Vector2(0, 0);
       classText.alignment = TextAnchor.LowerLeft;
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