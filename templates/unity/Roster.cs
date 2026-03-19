using System.Collections.Generic;
using UnityEngine;
using System.IO;

[System.Serializable]
public class CharacterStats {
    public float speed;
    public float acceleration;
    public float visionRadius;
    public float trapResistance;
    public int baseLives;
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
public class ShopItem {
    public string id;
    public string name;
    public string description;
    public int cost;
}

[System.Serializable]
public class Roster {
    public List<CharacterClass> classes;
    public List<ShopItem> items;

    public static Roster Load(string path) {
        if (!File.Exists(path)) return null;
        string json = File.ReadAllText(path);
        return JsonUtility.FromJson<Roster>(json);
    }
}