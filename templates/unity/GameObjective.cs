using UnityEngine;

public enum ObjectiveType { ExitPortal, Coin }

public class GameObjective : MonoBehaviour {
    public Vector2Int gridPos;
    public ObjectiveType type;

    void Update() {
        if (GameManager.Instance == null || GameManager.Instance.agent == null) return;
        if (GameManager.Instance.agent.gridPos == gridPos) {

            if (type == ObjectiveType.ExitPortal) {
                Debug.Log("Meta alcançada!");
                GameManager.Instance.OnGoalReached();
            } else {
                Debug.Log("Moeda obtida!");
                GameManager.Instance.OnCollect(gridPos);
            }
            Destroy(gameObject); // Desaparece do mapa
        }
    }
}