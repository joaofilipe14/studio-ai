using UnityEngine;

public class Collectible : MonoBehaviour
{
    private void OnTriggerEnter(Collider other)
    {
        // Verifica se quem tocou na moeda foi o Agente
        // Nota: Garante que o teu Prefab do Agente tem a Tag "Player"
        if (other.CompareTag("Player") || other.gameObject.name == "Agent")
        {
            // Avisa o GameManager que uma moeda foi coletada
            if (GameManager.Instance != null)
            {
                GameManager.Instance.OnCollectiblePickedUp();

                // Feedback visual opcional no console
                Debug.Log("Item coletado!");
            }

            // Destrói a moeda para que não possa ser coletada duas vezes
            Destroy(gameObject);
        }
    }
}