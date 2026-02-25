using UnityEngine;

public enum PowerUpType { Time, Speed }

public class PowerUp : MonoBehaviour {
    public PowerUpType type;
    public Vector2Int gridPos;

    void Update()
    {
        // Se o GameManager não existir ou a ronda terminou, não faz nada
        if (GameManager.Instance == null || GameManager.Instance.finished) return;

        // VERIFICAÇÃO POR GRELHA: O Agente está na mesma posição que este Power-up?
        if (GameManager.Instance.agent != null && GameManager.Instance.agent.gridPos == gridPos)
        {
            ApplyEffect();
            Destroy(gameObject); // Desaparece imediatamente após a recolha
        }
    }

    void ApplyEffect()
    {
        if (type == PowerUpType.Time)
        {
            GameManager.Instance.AddExtraTime();
        }
        else if (type == PowerUpType.Speed)
        {
            GameManager.Instance.ApplySpeedBoost();
        }
    }
}