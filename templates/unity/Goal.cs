using UnityEngine;

public class Goal : MonoBehaviour
{
    public Vector2Int gridPos;

    void Update()
    {
        if (GameManager.Instance == null || GameManager.Instance.agent == null) return;
        Debug.Log("GOAL");
        // Se o Agente pisar a mesma célula que o Goal, ganha imediatamente!
        if (GameManager.Instance.agent.gridPos == gridPos)
        {
            GameManager.Instance.OnGoalReached();
            Destroy(gameObject);
        }
    }
}