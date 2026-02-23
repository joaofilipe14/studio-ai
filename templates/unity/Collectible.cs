using UnityEngine;

public class Collectible : MonoBehaviour
{
    // Armazena a posição lógica na grelha
    public Vector2Int gridPos;

    void Update()
    {
        // Segurança: verifica se o GameManager e o Agente estão ativos
        if (GameManager.Instance == null || GameManager.Instance.agent == null) return;

        // Compara a posição do agente com a posição desta moeda
        if (GameManager.Instance.agent.gridPos == gridPos)
        {
            // Notifica o Manager para aumentar a pontuação e gerar nova moeda
            GameManager.Instance.OnCollect(gridPos);

            // Remove o objeto da cena
            Destroy(gameObject);
        }
    }
}