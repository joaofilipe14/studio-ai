using System.Collections.Generic;
using UnityEngine;
using System.IO;

[System.Serializable]
public class SafeRoomItem {
    public string id;
    public string name;
    public string description;
    public string rarity; // "Common", "Uncommon" ou "Rare"
    public int cost;
    public string effectType;
    public float effectValue;
}

[System.Serializable]
public class SafeRoomCatalog {
    public List<SafeRoomItem> safeRoomItems;

    public static SafeRoomCatalog Load(string path) {
        if (!File.Exists(path)) {
            Debug.LogWarning("Ficheiro safe_room_items.json não encontrado em: " + path);
            return null;
        }
        string json = File.ReadAllText(path);
        return JsonUtility.FromJson<SafeRoomCatalog>(json);
    }
}