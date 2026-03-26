using System.Collections.Generic;
using UnityEngine;
using System.IO;

[System.Serializable]
public class PlayerWallet {
    public int totalCoins;
    public int timeCrystals;
}

[System.Serializable]
public class PlayerLoadout {
    public string selectedClassID;
}

[System.Serializable]
public class PlayerUpgrades {
    public int startExtraTimeLvl;
    public int morePowerUpsLvl;
    public int permSpeedLvl;
    public int trapReductionLvl;
}

[System.Serializable]
public class PlayerStats {
    public int totalTrapsHit;
    public int totalWins;
    public int currentLives;
    public int maxLives;
    public int basePowerUpCount;
    public bool hasSeenTutorial;
}

[System.Serializable]
public class PlayerSave {
    public string playerName;
    public int currentCampaignLevel;
    public PlayerWallet wallet;
    public PlayerLoadout loadout;
    public List<string> unlockedClasses;
    public PlayerUpgrades purchasedUpgrades;
    public PlayerStats stats;

    // 🚨 AQUI ESTÁ A NOSSA GAVETA NOVA QUE FALTAVA!
    public List<ItemPurchase> purchasedItems = new List<ItemPurchase>();

    public static PlayerSave Load(string path) {
        if (!File.Exists(path)) {
            return new PlayerSave {
                playerName = "New Player",
                currentCampaignLevel = 1,
                wallet = new PlayerWallet(),
                loadout = new PlayerLoadout { selectedClassID = "Explorer" },
                stats = new PlayerStats { currentLives = 3, maxLives = 3 },
                purchasedItems = new List<ItemPurchase>() // 🚨 Garante que não fica a zero num save novo
            };
        }
        string json = File.ReadAllText(path);
        return JsonUtility.FromJson<PlayerSave>(json);
    }

    public void Save(string path) {
        string json = JsonUtility.ToJson(this, true);
        File.WriteAllText(path, json);
    }
}