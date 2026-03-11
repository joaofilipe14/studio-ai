using System.Collections.Generic;
using UnityEngine;
using System.IO;

// ==========================================
// TRUQUE MÁGICO PARA LER ARRAYS JSON NO UNITY
// ==========================================
public static class JsonHelper {
    public static T[] FromJson<T>(string json) {
        // Embrulha o array num objeto temporário para o Unity conseguir ler
        string newJson = "{ \"array\": " + json + "}";
        Wrapper<T> wrapper = JsonUtility.FromJson<Wrapper<T>>(newJson);
        return wrapper.array;
    }

    [System.Serializable]
    private class Wrapper<T> {
        public T[] array;
    }
}

// ==========================================
// 1. LEVEL GENOME (Agora adaptado para Listas)
// ==========================================
[System.Serializable]
public class LevelArena {
    public float halfSize;
    public bool walls;
}

[System.Serializable]
public class LevelObstacles {
    public int count;
    public float minScale;
    public float maxScale;
}

[System.Serializable]
public class LevelRules {
    public float timeLimit;
    public int targetCount;
    public int enemyCount;
    public float enemySpeed;
    public int powerUpCount;
    public string powerUpType;
    public int trapCount;
    public float trapPenalty;
}

[System.Serializable]
public class LevelGenome {
    public int level_id;
    public int seed;
    public string theme;
    public LevelArena arena;
    public LevelObstacles obstacles;
    public LevelRules rules;
}

// ==========================================
// 2. ROSTER (Catálogo de Classes - Estático)
// ==========================================
[System.Serializable]
public class CharacterStats {
    public float speed;
    public float acceleration;
    public float visionRadius;
    public float trapResistance;
}

[System.Serializable]
public class CharacterClass {
    public string id;
    public string name;
    public string description;
    public string spriteName;
    public int cost;
    public CharacterStats stats;
}

[System.Serializable]
public class Roster {
    public List<CharacterClass> classes;

    public static Roster Load(string path) {
        if (!File.Exists(path)) return null;
        string json = File.ReadAllText(path);
        return JsonUtility.FromJson<Roster>(json);
    }
}

// ==========================================
// 3. PLAYER SAVE (Progresso do Jogador)
// ==========================================
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
}

[System.Serializable]
public class PlayerStats {
    public int totalTrapsHit;
    public int totalWins;
    public int currentLives; // Vidas atuais
    public int maxLives;     // O máximo de vidas que pode carregar
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

    public static PlayerSave Load(string path) {
        if (!File.Exists(path)) {
            return new PlayerSave {
                playerName = "New Player",
                currentCampaignLevel = 1,
                wallet = new PlayerWallet(),
                loadout = new PlayerLoadout { selectedClassID = "Explorer" },
                stats = new PlayerStats { currentLives = 3, maxLives = 3 } // COMEÇA COM 3 VIDAS!
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