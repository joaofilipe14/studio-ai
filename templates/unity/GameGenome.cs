using UnityEngine;

// Truque para ler Arrays JSON
public static class JsonHelper {
    public static T[] FromJson<T>(string json) {
        string newJson = "{ \"array\": " + json + "}";
        Wrapper<T> wrapper = JsonUtility.FromJson<Wrapper<T>>(newJson);
        return wrapper.array;
    }

    [System.Serializable]
    private class Wrapper<T> {
        public T[] array;
    }
}

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