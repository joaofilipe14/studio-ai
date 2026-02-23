using UnityEngine;

public class Goal : MonoBehaviour
{
    private void OnTriggerEnter(Collider other)
    {
        // Tenta obter o script do agente para confirmar quem colidiu
        SimpleAgent agent = other.GetComponent<SimpleAgent>();

        // Verifica se o agente é válido e se o GameManager existe
        if (agent != null && GameManager.Instance != null)
        {
            // Chama a função de vitória no GameManager
            GameManager.Instance.OnGoalReached();
        }
    }
}