using UnityEngine;
using UnityEngine.AI;

public class ChaserAI : MonoBehaviour
{
    public Transform target;
    private NavMeshAgent agent;

    void Start() => agent = GetComponent<NavMeshAgent>();

    void Update()
    {
        if (target != null && agent.isOnNavMesh)
            agent.SetDestination(target.position);
    }

    void OnTriggerEnter(Collider other)
    {
        if (other.CompareTag("Player"))
        {
            Debug.Log("Agente apanhado pelo inimigo!");
            // Notifica o GameManager que o agente "morreu" (podes contar como Timeout ou Stuck)
            GameManager.Instance.NotifyStuck();
        }
    }
}