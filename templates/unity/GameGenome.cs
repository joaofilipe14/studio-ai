using System;
using UnityEngine;
using System.IO;

[Serializable]
public class ArenaData {
    public float halfSize = 8.0f;
    public bool walls = true;
}

[Serializable]
public class AgentData {
    public float speed = 5.0f;
    public float acceleration = 15.0f;
    public float stopDistance = 0.5f;
}

[Serializable]
public class ObstaclesData {
    public int count = 8;
    public float minScale = 1.0f;
    public float maxScale = 2.5f;
    public string type = "Static";
}

[Serializable]
public class RulesData {
    public float timeLimit = 20.0f;
    public int rounds = 5;
    public int targetCount = 1;
    public float enemySpeed = 0.0f;
    public float powerUpChance = 0.1f;
    public string powerUpType = "Mixed";
    public float trapChance = 0.05f;
    public float trapPenalty = 2.0f;
}


// Representa UMA configuração de jogo (Um Modo)
[Serializable]
public class GameGenome {
    public string mode = "PointToPoint";
    public int seed = 42;
    public ArenaData arena;
    public AgentData agent;
    public ObstaclesData obstacles;
    public RulesData rules;

    public void Validate() {
        if (arena == null) arena = new ArenaData();
        if (agent == null) agent = new AgentData();
        if (obstacles == null) obstacles = new ObstaclesData();
        if (rules == null) rules = new RulesData();
    }
}

// Representa o ficheiro JSON inteiro com a Lista de Modos
[Serializable]
public class GameGenomeCollection {
    public GameGenome[] configs;
    public string mode;
    public bool userControl;

    public static GameGenomeCollection Load(string path) {
        if (File.Exists(path)) {
            string json = File.ReadAllText(path);

            GameGenomeCollection collection = JsonUtility.FromJson<GameGenomeCollection>(json);

            if (collection == null || collection.configs == null || collection.configs.Length == 0) {
                GameGenome single = JsonUtility.FromJson<GameGenome>(json);
                if (single != null) {
                    single.Validate();
                    return new GameGenomeCollection {
                        configs = new GameGenome[] { single },
                        mode = single.mode, // Fallback
                        userControl = false // Fallback
                    };
                }
            } else {
                foreach(var c in collection.configs) c.Validate();
                return collection;
            }
        }

        Debug.LogWarning("Genome file not found at " + path + ". Using default values.");
        var defaultGenome = new GameGenome();
        defaultGenome.Validate();
        return new GameGenomeCollection {
            configs = new GameGenome[] { defaultGenome },
            mode = defaultGenome.mode,
            userControl = false
        };
    }

    public GameGenome GetConfig(string modeName) {
        if (configs == null) return null;
        foreach (var c in configs) {
            if (c.mode == modeName) return c;
        }
        return configs.Length > 0 ? configs[0] : null;
    }
}