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
    public bool userControl = false;
}

[Serializable]
public class ObstaclesData {
    public int count = 8;
    public float minScale = 1.0f;
    public float maxScale = 2.5f;
    public string type = "Static"; // Novo: Para futuros obstáculos móveis ou destrutíveis
}

[Serializable]
public class RulesData {
    public float timeLimit = 20.0f;
    public int rounds = 5;
    public int targetCount = 1;    // Novo: Quantidade de moedas/objetivos para o modo Collect
    public float enemySpeed = 0.0f; // Novo: Para o futuro modo Survival
}

[Serializable]
public class GameGenome {
    public string mode = "PointToPoint"; // Novo: Define o motor de regras ("PointToPoint", "Collect")
    public int seed = 42;
    public ArenaData arena;
    public AgentData agent;
    public ObstaclesData obstacles;
    public RulesData rules;

    public static GameGenome Load(string path) {
        if (File.Exists(path)) {
            string json = File.ReadAllText(path);
            GameGenome loaded = JsonUtility.FromJson<GameGenome>(json);

            // Garantir que as sub-classes não fiquem nulas se o JSON for parcial
            if (loaded.arena == null) loaded.arena = new ArenaData();
            if (loaded.agent == null) loaded.agent = new AgentData();
            if (loaded.obstacles == null) loaded.obstacles = new ObstaclesData();
            if (loaded.rules == null) loaded.rules = new RulesData();

            Debug.Log($"Genome loaded! Mode: {loaded.mode}, Seed: {loaded.seed}");
            return loaded;
        }

        Debug.LogWarning("Genome file not found at " + path + ". Using default values.");
        return new GameGenome() {
            mode = "PointToPoint",
            arena = new ArenaData(),
            agent = new AgentData(),
            obstacles = new ObstaclesData(),
            rules = new RulesData()
        };
    }
}