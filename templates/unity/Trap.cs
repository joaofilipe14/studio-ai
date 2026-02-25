using UnityEngine;

public class Trap : MonoBehaviour {
    public Vector2Int gridPos;
    public float penalty = 2.0f;
    private bool activated = false;

    void Update() {
        if (GameManager.Instance == null || GameManager.Instance.finished || activated) return;

        // Verifica se o Agente pisou a armadilha
        if (GameManager.Instance.agent != null && GameManager.Instance.agent.gridPos == gridPos) {
            TriggerTrap();
        }
    }

    void TriggerTrap() {
        activated = true;
        GameManager.Instance.ApplyTrapPenalty(penalty);

        // Feedback visual: a armadilha muda de cor ou afunda
        GetComponent<Renderer>().material.color = Color.black;
        Destroy(gameObject, 0.5f); // Desaparece após ser ativada
    }
}