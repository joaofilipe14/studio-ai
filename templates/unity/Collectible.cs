using UnityEngine;

public class Collectible : MonoBehaviour {
    // Armazena a posição lógica na grelha
    public Vector2Int gridPos;

    void Update() {
        if (GameManager.Instance == null || GameManager.Instance.agent == null) return;
        if (GameManager.Instance.agent.gridPos == gridPos) {
            Debug.Log("Moeda obtida.");
            GameManager.Instance.OnCollect(gridPos);
            Destroy(gameObject);
        }
    }
}