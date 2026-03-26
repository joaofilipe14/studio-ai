using UnityEngine;
using UnityEngine.UIElements;
using System;

public class UIManager : MonoBehaviour {
    public static UIManager Instance { get; private set; }
    public enum UIState { None, Title, Vault, HUD, EndScreen, Pause }
    public UIState currentState = UIState.None;
    private UIDocument uiDocument;
    private Label timerLabel;
    private Label scoreLabel;
    private Label livesLabel;
    private Label levelLabel;
    private string currentVaultTab = "classes";

    void Awake() {
        if (Instance == null) Instance = this;
        GameObject uiObj = new GameObject("UI_Toolkit_Root");
        uiObj.transform.SetParent(this.transform);
        uiDocument = uiObj.AddComponent<UIDocument>();
        PanelSettings ps = Resources.Load<PanelSettings>("UI/DefaultPanelSettings");
        if (ps != null) uiDocument.panelSettings = ps;
    }

    void Start() {
        if (Application.isBatchMode || GameManager.Instance.isTrailerMode || !GameManager.Instance.userControl) {
            ShowHUD();
            GameManager.Instance.StartNewRun();
        } else {
            ShowTitleScreen();
        }
    }

    public void HideUIForTrailer() {
        if (uiDocument != null && uiDocument.rootVisualElement != null) {
            uiDocument.rootVisualElement.style.display = DisplayStyle.None;
        }
    }

    public void ShowTitleScreen() {
        Debug.Log($"ShowTitleScreen");
        currentState = UIState.Title;
        UnityEngine.Cursor.visible = true;
        UnityEngine.Cursor.lockState = CursorLockMode.None;

        VisualTreeAsset uxml = Resources.Load<VisualTreeAsset>("UI/MainMenu");

        if (uxml != null) {
            uiDocument.visualTreeAsset = uxml;
            var root = uiDocument.rootVisualElement;
            root.style.display = DisplayStyle.Flex;

            int moedas = GameManager.Instance.currentPlayer != null ? GameManager.Instance.currentPlayer.wallet.totalCoins : 0;
            int cristais = GameManager.Instance.currentPlayer != null ? GameManager.Instance.currentPlayer.wallet.timeCrystals : 0;
            Label txtStats = root.Q<Label>("txt-stats");
            if (txtStats != null) txtStats.text = $"Moedas: {moedas} | Cristais: {cristais}";

            Button btnPlay = root.Q<Button>("btn-play");
            if (btnPlay != null) btnPlay.clicked += () => { GameManager.Instance.StartNewRun(); };

            Button btnVault = root.Q<Button>("btn-vault");
            if (btnVault != null) btnVault.clicked += ShowVaultScreen;

            Button btnQuit = root.Q<Button>("btn-quit");
            if (btnQuit != null) btnQuit.clicked += () => Application.Quit();
        }
    }

    public void ShowHUD() {
        currentState = UIState.HUD;
        VisualTreeAsset uxml = Resources.Load<VisualTreeAsset>("UI/HUD");
        uiDocument.visualTreeAsset = uxml;
        var root = uiDocument.rootVisualElement;
        root.style.display = DisplayStyle.Flex;

        livesLabel = root.Q<Label>("txt-lives");
        if (livesLabel != null && GameManager.Instance.currentPlayer != null) {
            livesLabel.text = GameManager.Instance.currentPlayer.stats.currentLives.ToString();
        }
        timerLabel = root.Q<Label>("txt-timer");
        scoreLabel = root.Q<Label>("txt-coins");
        levelLabel = root.Q<Label>("txt-level");
        if (levelLabel != null && GameManager.Instance.currentLevel != null) {
            levelLabel.text = "Nível " + GameManager.Instance.currentLevel.level_id.ToString();
        }
        RefreshActiveBuffsHUD();
    }

    public void RefreshActiveBuffsHUD() {
        VisualElement root = uiDocument.rootVisualElement;
        if (root == null) return;

        VisualElement containerLeft = root.Q<VisualElement>("active-buffs-left");
        VisualElement containerRight = root.Q<VisualElement>("active-buffs-right");

        if (containerLeft != null) containerLeft.Clear();
        if (containerRight != null) containerRight.Clear();

        PlayerSave save = GameManager.Instance.currentPlayer;

        // --- 1. PERMANENTES (ESQUERDA) ---
        if (save != null && save.purchasedItems != null && containerLeft != null) {
            foreach (var permItem in save.purchasedItems) {
                if (permItem.quantity <= 0) continue;

                string cssClass = $"icon-{permItem.itemID.Replace("_", "-").ToLower()}";
                AddBuffIconToHUD(containerLeft, cssClass, permItem.quantity, "Perm", true);
            }
        }

        // --- 2. TEMPORÁRIOS (DIREITA) ---
        if (GameManager.Instance.tempPurchasedItems != null && containerRight != null) {
            foreach (var tempItem in GameManager.Instance.tempPurchasedItems) {
                if (tempItem.quantity <= 0) continue;

                string cssClass = $"icon-{tempItem.itemID.Replace("_", "-").ToLower()}";
                string rarity = "Common";
                if (tempItem.itemID.Contains("uncommon")) rarity = "Uncommon";
                else if (tempItem.itemID.Contains("rare")) rarity = "Rare";

                // 🚨 AQUI: Adicionamos "false" porque queremos o ícone espelhado à direita
                AddBuffIconToHUD(containerRight, cssClass, tempItem.quantity, rarity, false);
            }
        }
    }

    private void AddBuffIconToHUD(VisualElement container, string cssClassName, int amount, string rarity, bool isLeft) {
        VisualElement icon = new VisualElement();
        icon.AddToClassList("hud-buff-icon");
        icon.AddToClassList(cssClassName);

        // 🚨 Adiciona a classe de espelho ao fundo da imagem (Left ou Right)
        icon.AddToClassList(isLeft ? "hud-buff-icon-left" : "hud-buff-icon-right");

        Color rarityColor = new Color(0f, 1f, 1f); // Cyano

        if (rarity == "Common") rarityColor = new Color(0.2f, 0.8f, 0.2f); // Verde
        else if (rarity == "Uncommon") rarityColor = new Color(0.2f, 0.4f, 1f); // Azul
        else if (rarity == "Rare") rarityColor = new Color(0.8f, 0.2f, 0.8f); // Roxo

        if (rarity != "Perm") {
            icon.style.borderBottomColor = new StyleColor(rarityColor);
        }

        Label amountLabel = new Label();
        amountLabel.AddToClassList("hud-buff-amount");

        // 🚨 Adiciona a classe de espelho à caixa preta do número (Left ou Right)
        amountLabel.AddToClassList(isLeft ? "hud-buff-amount-left" : "hud-buff-amount-right");

        if (rarity == "Perm") amountLabel.text = $"Lv{amount}";
        else amountLabel.text = $"x{amount}";

        amountLabel.style.color = rarityColor;

        icon.Add(amountLabel);
        container.Add(icon);
    }

    public void ShowPauseMenu() {
        currentState = UIState.Pause;
        UnityEngine.Cursor.visible = true;
        UnityEngine.Cursor.lockState = CursorLockMode.None;
        VisualTreeAsset uxml = Resources.Load<VisualTreeAsset>("UI/EndScreen");
        uiDocument.visualTreeAsset = uxml;
        var root = uiDocument.rootVisualElement;

        Label txtTitle = root.Q<Label>("txt-title");
        Label txtReason = root.Q<Label>("txt-reason");
        Button btnAction = root.Q<Button>("btn-action");
        Button btnMenu = root.Q<Button>("btn-menu");
        VisualElement panel = root.Q<VisualElement>(className: "end-panel");

        txtTitle.text = "JOGO PAUSADO";
        txtTitle.style.color = new Color(0f, 0.8f, 1f);
        panel.style.borderTopColor = new Color(0f, 0.8f, 1f);
        txtReason.text = "O relógio está parado. \nRespira fundo e planeia a tua rota.";
        btnAction.text = "CONTINUAR";
        btnAction.style.borderBottomColor = new Color(0f, 0.8f, 1f);
        btnAction.clicked += () => GameManager.Instance.TogglePause();
        btnMenu.style.display = DisplayStyle.None;
    }

    public void ShowEndScreen(bool victory, string reason) {
        currentState = UIState.EndScreen;
        UnityEngine.Cursor.visible = true;
        UnityEngine.Cursor.lockState = CursorLockMode.None;

        VisualTreeAsset uxml = Resources.Load<VisualTreeAsset>("UI/EndScreen");
        int currentLvl = GameManager.Instance.currentLevel != null ? GameManager.Instance.currentLevel.level_id : 1;

        if (uxml != null) {
            uiDocument.visualTreeAsset = uxml;
            var root = uiDocument.rootVisualElement;

            Label txtTitle = root.Q<Label>("txt-title");
            Label txtReason = root.Q<Label>("txt-reason");
            Button btnAction = root.Q<Button>("btn-action");
            Button btnMenu = root.Q<Button>("btn-menu");
            VisualElement panel = root.Q<VisualElement>(className: "end-panel");

            txtReason.text = reason;

            if (victory) {
                txtTitle.text = $"NÍVEL {currentLvl} CONCLUÍDO!";
                txtTitle.style.color = new Color(0.2f, 1f, 0.2f);
                panel.style.borderTopColor = new Color(0.2f, 1f, 0.2f);
                btnAction.text = "PRÓXIMO NÍVEL";
                btnAction.style.borderBottomColor = new Color(0.2f, 1f, 0.2f);
                btnAction.clicked += () => GameManager.Instance.UI_PlayNextLevel();
                btnMenu.style.display = DisplayStyle.None;
            } else {
                txtTitle.text = $"MORRESTE NO NÍVEL {currentLvl}!";
                txtTitle.style.color = new Color(1f, 0.2f, 0.2f);
                panel.style.borderTopColor = new Color(1f, 0.2f, 0.2f);
                btnAction.text = "TENTAR NOVAMENTE";
                btnAction.style.borderBottomColor = new Color(1f, 0.2f, 0.2f);
                btnAction.clicked += () => GameManager.Instance.UI_PlayNextLevel();
                btnMenu.style.display = DisplayStyle.Flex;
            }
            btnMenu.clicked += () => GameManager.Instance.UI_ReturnToMenu();

        } else {
            if (victory) GameManager.Instance.UI_PlayNextLevel();
            else GameManager.Instance.UI_ReturnToMenu();
        }
    }

    public void ShowVaultScreen() {
        currentState = UIState.Vault;
        VisualTreeAsset uxml = Resources.Load<VisualTreeAsset>("UI/VaultScreen");
        if (uxml == null) { ShowTitleScreen(); return; }

        uiDocument.visualTreeAsset = uxml;
        var root = uiDocument.rootVisualElement;

        var player = GameManager.Instance.currentPlayer;

        // 1. Configura os Botões das Abas
        Button btnClasses = root.Q<Button>("btn-tab-classes");
        Button btnUpgrades = root.Q<Button>("btn-tab-upgrades");

        if (btnClasses != null) btnClasses.clicked += () => { currentVaultTab = "classes"; RefreshVaultUI(root); };
        if (btnUpgrades != null) btnUpgrades.clicked += () => { currentVaultTab = "upgrades"; RefreshVaultUI(root); };

        // 2. Primeira atualização
        RefreshVaultUI(root);

        Button btnBack = root.Q<Button>("btn-back");
        if (btnBack != null) btnBack.clicked += ShowTitleScreen;
    }

    private void RefreshVaultUI(VisualElement root) {
        var player = GameManager.Instance.currentPlayer;

        // 1. Atualiza os Stats no topo
        Label txtStats = root.Q<Label>("txt-vault-stats");
        if (txtStats != null) {
            // Usamos emojis ou símbolos para manter o estilo limpo que definimos
            txtStats.text = $"💎 {player.wallet.timeCrystals}   |   ❤️ Max: {player.stats.maxLives}";
        }

        // 2. Controla o aspeto visual das Abas (Quem está aceso?)
        Button btnClasses = root.Q<Button>("btn-tab-classes");
        Button btnUpgrades = root.Q<Button>("btn-tab-upgrades");

        if (currentVaultTab == "classes") {
            btnClasses.AddToClassList("tab-active");
            btnUpgrades.RemoveFromClassList("tab-active");
        } else {
            btnUpgrades.AddToClassList("tab-active");
            btnClasses.RemoveFromClassList("tab-active");
        }

        // 3. Limpa e Preenche o Contentor Único
        VisualElement container = root.Q<VisualElement>("items-container"); // O ID que deixámos no UXML
        if (container != null) {
            container.Clear();

            if (currentVaultTab == "classes") {
                foreach (var c in GameManager.Instance.roster.classes) {
                    container.Add(GenerateClassCard(c, player));
                }
            } else {
                foreach (var item in GameManager.Instance.roster.items) {
                    container.Add(GenerateItemCard(item, player));
                }
            }
        }
    }

    private VisualElement GenerateClassCard(CharacterClass c, PlayerSave save) {
        VisualElement card = new VisualElement();
        card.AddToClassList("card");

        card.Add(new Label(c.name) { name = "title", tooltip = c.name });
        card.Q<Label>("title").AddToClassList("card-title");

        VisualElement icon = new VisualElement();
        icon.AddToClassList("card-img");
        icon.AddToClassList(!string.IsNullOrEmpty(c.spriteName) ? $"icon-{c.spriteName.Replace("Sprite", "").ToLower()}" : "icon-default");
        card.Add(icon);

        Label desc = new Label(c.description);
        desc.AddToClassList("card-desc");
        card.Add(desc);

        Button btn = new Button();
        btn.AddToClassList("btn");

        bool isUnlocked = save.unlockedClasses != null && save.unlockedClasses.Contains(c.id) || c.cost == 0;
        bool isEquipped = save.loadout.selectedClassID == c.id;

        if (isEquipped) {
            btn.text = "✔ EQUIPADO";
            btn.AddToClassList("cyberpunk-green");
            btn.style.color = new Color(0.2f, 1f, 0.2f);
        } else if (isUnlocked) {
            btn.text = "EQUIPAR";
            btn.AddToClassList("cyberpunk-gray");
            btn.clicked += () => {
                save.loadout.selectedClassID = c.id;
                GameManager.Instance.SetSelectedClass(c);
                SaveAndRefresh();
            };
        } else {
            btn.text = $"COMPRAR ({c.cost} 💠)";
            btn.AddToClassList("cyberpunk-blue");
            btn.clicked += () => {
                if (save.wallet.timeCrystals >= c.cost) {
                    save.wallet.timeCrystals -= c.cost;
                    if (save.unlockedClasses == null) save.unlockedClasses = new System.Collections.Generic.List<string>();
                    save.unlockedClasses.Add(c.id);
                    save.loadout.selectedClassID = c.id;
                    GameManager.Instance.SetSelectedClass(c);
                    SaveAndRefresh();
                } else {
                    Debug.Log("Cristais insuficientes!");
                }
            };
        }

        card.Add(btn);
        return card;
    }

    private VisualElement GenerateItemCard(ShopItem item, PlayerSave save) {
        VisualElement card = new VisualElement();
        card.AddToClassList("card");

        // 1. DESCOBRIR QUANTOS JÁ COMPRÁMOS
        int amountBought = 0;
        if (save.purchasedItems != null) {
            var purchaseRecord = save.purchasedItems.Find(p => p.itemID == item.id);
            if (purchaseRecord != null) {
                amountBought = purchaseRecord.quantity;
            }
        }

        // 2. TÍTULO DA CARTA
        Label title = new Label(item.name);
        title.AddToClassList("card-title");
        card.Add(title);

        // 3. ÍCONE DINÂMICO
        VisualElement icon = new VisualElement();
        icon.AddToClassList("card-img");
        string autoClassName = $"icon-{item.id.Replace("_", "-").ToLower()}";
        icon.AddToClassList(autoClassName);

        // 4. ADICIONA O CONTADOR REDONDO SE JÁ TIVER COMPRADO PELO MENOS 1
        if (amountBought > 0) {
            Label counterLabel = new Label(amountBought.ToString());
            counterLabel.AddToClassList("icon-counter"); // A nossa classe CSS
            icon.Add(counterLabel);
        }
        card.Add(icon);

        // 5. DESCRIÇÃO
        Label desc = new Label(item.description);
        desc.AddToClassList("card-desc");
        card.Add(desc);

        // 6. VERIFICA OS LIMITES (HARD CAPS)
        bool isMaxedOut = false;
        if (save.purchasedUpgrades == null) save.purchasedUpgrades = new PlayerUpgrades();

        if (item.id == "item_life" && save.stats.maxLives >= 7) isMaxedOut = true;
        else if (item.id == "item_perm_speed" && save.purchasedUpgrades.permSpeedLvl >= 5) isMaxedOut = true;
        else if (item.id == "item_trap_reduction" && save.purchasedUpgrades.trapReductionLvl >= 5) isMaxedOut = true;
        else if (item.id == "item_time_boost" && save.purchasedUpgrades.startExtraTimeLvl >= 5) isMaxedOut = true;

        // 7. CRIA O BOTÃO DE COMPRA OU BOTÃO "MÁXIMO"
        Button btn = new Button();
        btn.AddToClassList("btn");

        if (isMaxedOut) {
            btn.text = "MÁXIMO";
            btn.style.backgroundColor = new StyleColor(new Color(0.3f, 0.3f, 0.3f));
            btn.style.color = new StyleColor(new Color(0.7f, 0.7f, 0.7f));
            btn.SetEnabled(false);
        } else {
            btn.AddToClassList("cyberpunk-blue");
            btn.text = $"COMPRAR ({item.cost} 💠)";

            btn.clicked += () => {
                if (save.wallet.timeCrystals >= item.cost) {
                    save.wallet.timeCrystals -= item.cost;

                    // Regista a compra na lista para o contador visual atualizar
                    if (save.purchasedItems == null) save.purchasedItems = new System.Collections.Generic.List<ItemPurchase>();
                    var purchase = save.purchasedItems.Find(p => p.itemID == item.id);
                    if (purchase != null) purchase.quantity++;
                    else save.purchasedItems.Add(new ItemPurchase { itemID = item.id, quantity = 1 });

                    // Aplica a melhoria real
                    if (item.id == "item_life") {
                        save.stats.maxLives++;
                        save.stats.currentLives++;
                    } else if (item.id == "item_time_boost") {
                        save.purchasedUpgrades.startExtraTimeLvl++;
                    } else if (item.id == "item_perm_speed") {
                        save.purchasedUpgrades.permSpeedLvl++;
                    } else if (item.id == "item_trap_reduction") {
                        save.purchasedUpgrades.trapReductionLvl++;
                    }

                    SaveAndRefresh();
                } else {
                    Debug.Log("Cristais insuficientes!");
                }
            };
        }

        card.Add(btn);
        return card;
    }

    public void ShowSafeRoomScreen() {
        currentState = UIState.EndScreen;
        UnityEngine.Cursor.visible = true;
        UnityEngine.Cursor.lockState = CursorLockMode.None;

        VisualTreeAsset uxml = Resources.Load<VisualTreeAsset>("UI/SafeRoomScreen");
        if (uxml == null) { GameManager.Instance.UI_PlayNextLevel(); return; } // Falha segura

        uiDocument.visualTreeAsset = uxml;
        var root = uiDocument.rootVisualElement;

        var player = GameManager.Instance.currentPlayer;
        int currentLvl = GameManager.Instance.currentLevel != null ? GameManager.Instance.currentLevel.level_id : 1;

        Label txtCoins = root.Q<Label>("txt-coins");
        if (txtCoins != null) txtCoins.text = $"Moedas: {player.wallet.totalCoins} 🪙";

        VisualElement itemsContainer = root.Q<VisualElement>("items-container");
        itemsContainer.Clear();
        var catalog = GameManager.Instance.safeRoomCatalog;
        if (catalog != null && catalog.safeRoomItems != null && catalog.safeRoomItems.Count > 0) {
            for (int i = 0; i < 3; i++) {
                SafeRoomItem drawnItem = DraftRandomItem(catalog.safeRoomItems, currentLvl, player);
                if (drawnItem != null) {
                    itemsContainer.Add(GenerateSafeRoomCard(drawnItem, player));
                }
            }
        }
        Button btnContinue = root.Q<Button>("btn-continue");
        if (btnContinue != null) {
            btnContinue.clicked += () => {
                player.Save(System.IO.Path.Combine(Application.dataPath, "..", "player_save.json"));
                GameManager.Instance.UI_PlayNextLevel();
            };
        }
    }

    private SafeRoomItem DraftRandomItem(System.Collections.Generic.List<SafeRoomItem> pool, int level, PlayerSave save) {
        int luckBoost = 0;
        float chanceCommon, chanceUncommon, chanceRare;
        if (level <= 4) {
            chanceCommon = 80f - luckBoost; chanceUncommon = 20f + (luckBoost/2f); chanceRare = 0f + (luckBoost/2f);
        } else if (level <= 7) {
            chanceCommon = 50f - luckBoost; chanceUncommon = 40f + (luckBoost/2f); chanceRare = 10f + (luckBoost/2f);
        } else {
            chanceCommon = 30f - luckBoost; chanceUncommon = 50f; chanceRare = 20f + luckBoost;
        }
        float roll = UnityEngine.Random.Range(0f, 100f);
        string targetRarity = "Common";
        if (roll > chanceCommon) targetRarity = "Uncommon";
        if (roll > chanceCommon + chanceUncommon) targetRarity = "Rare";
        var filteredPool = pool.FindAll(item => item.rarity == targetRarity);

        if (filteredPool.Count > 0) {
            return filteredPool[UnityEngine.Random.Range(0, filteredPool.Count)];
        }
        return pool[UnityEngine.Random.Range(0, pool.Count)];
    }

    private VisualElement GenerateSafeRoomCard(SafeRoomItem item, PlayerSave save) {
        VisualElement card = new VisualElement();
        card.AddToClassList("card");

        // 1. Define as cores da Raridade
        Color rarityColor = new Color(0.8f, 0.8f, 0.8f); // Comum: Cinza Claro
        if (item.rarity == "Uncommon") rarityColor = new Color(0f, 0.8f, 1f); // Incomum: Azul Ciano
        if (item.rarity == "Rare") rarityColor = new Color(1f, 0.2f, 1f); // Raro: Roxo Néon

        card.style.borderTopColor = rarityColor;
        card.style.borderBottomColor = rarityColor;

        Label title = new Label(item.name);
        title.AddToClassList("card-title");
        title.style.color = rarityColor; // O título também ganha a cor
        card.Add(title);

        VisualElement icon = new VisualElement();
        icon.AddToClassList("card-img");
        string cssClass = $"icon-{item.id.Replace("_", "-").ToLower()}";
        icon.AddToClassList(cssClass);

        icon.style.borderTopColor = rarityColor;
        icon.style.borderBottomColor = rarityColor;
        icon.style.borderLeftColor = rarityColor;
        icon.style.borderRightColor = rarityColor;
        icon.style.backgroundColor = new Color(rarityColor.r, rarityColor.g, rarityColor.b, 0.15f);

        card.Add(icon);

        Label desc = new Label(item.description);
        desc.AddToClassList("card-desc");
        card.Add(desc);

        Button btn = new Button();
        btn.AddToClassList("btn-buy");
        btn.text = $"COMPRAR ({item.cost} 🪙)";

        btn.clicked += () => {
            if (save.wallet.totalCoins >= item.cost) {
                save.wallet.totalCoins -= item.cost;
                Debug.Log($"[SAFE ROOM] Compraste: {item.name} | Efeito: {item.effectType} {item.effectValue}");
                if (item.effectType == "SpeedBoost") {
                    GameManager.Instance.currentRunSpeedMultiplier *= item.effectValue;
                } else if (item.effectType == "VisionBoost") {
                    GameManager.Instance.currentRunVisionBonus += item.effectValue;
                } else if (item.effectType == "TrapReduction") {
                    GameManager.Instance.currentRunTrapMultiplier *= item.effectValue;
                }
                if (GameManager.Instance.tempPurchasedItems == null) {
                    GameManager.Instance.tempPurchasedItems = new System.Collections.Generic.List<ItemPurchase>();
                }
                var purchase = GameManager.Instance.tempPurchasedItems.Find(p => p.itemID == item.id);
                if (purchase != null) purchase.quantity++;
                else GameManager.Instance.tempPurchasedItems.Add(new ItemPurchase { itemID = item.id, quantity = 1 });

                btn.text = "ESGOTADO";
                btn.SetEnabled(false);
                btn.style.backgroundColor = new Color(0.2f, 0.2f, 0.2f);

                var root = uiDocument.rootVisualElement;
                Label txtCoins = root.Q<Label>("txt-coins");
                if (txtCoins != null) txtCoins.text = $"Moedas: {save.wallet.totalCoins} 🪙";

            } else {
                Debug.Log("Moedas insuficientes!");
                btn.text = "SEM FUNDOS";
            }
        };

        card.Add(btn);
        return card;
    }

    private void SaveAndRefresh() {
        GameManager.Instance.currentPlayer.Save(System.IO.Path.Combine(Application.dataPath, "..", "player_save.json"));
        ShowVaultScreen();
    }

    void Update() {
        if (currentState == UIState.HUD && GameManager.Instance != null && !GameManager.Instance.finished) {
            if (timerLabel != null) {
                float t = GameManager.Instance.currentTimer;
                timerLabel.text = $"Tempo: {t:F1}s";
                timerLabel.style.color = t <= 10f ? Color.red : Color.white;
            }
            if (scoreLabel != null && GameManager.Instance.currentPlayer != null) {
                int totalCoins = GameManager.Instance.currentPlayer.wallet.totalCoins + GameManager.Instance.collectedInRound;
                int totalCrystals = GameManager.Instance.currentPlayer.wallet.timeCrystals;
                scoreLabel.text = $"{totalCoins} 🪙    |   💎 {totalCrystals}";
            }
            if (livesLabel != null && GameManager.Instance.currentPlayer != null) {
                livesLabel.text = GameManager.Instance.currentPlayer.stats.currentLives.ToString();
            }
            if (levelLabel != null && GameManager.Instance.currentLevel != null) {
                levelLabel.text = "Nível " + GameManager.Instance.currentLevel.level_id.ToString();
            }
        }
    }
}