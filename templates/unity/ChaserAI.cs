using UnityEngine;
using System.Collections.Generic;

public class ChaserAI : MonoBehaviour {
    public GridWorld world;
    public Vector2Int gridPos;
    public float moveSpeed = 3.5f;
    private List<Vector2Int> path = new List<Vector2Int>();

    void Update() {
        if (world == null || GameManager.Instance == null || GameManager.Instance.agent == null || GameManager.Instance.finished)
            return;

        Vector2Int targetPos = GameManager.Instance.agent.gridPos;

        if (world.TryFindPath(gridPos, targetPos, path) && path.Count > 1) {
            Vector3 targetWorld = world.GridToWorld(path[1], transform.position.y);

            // 1. Calcula a direção e distância para o centro da próxima casa
            Vector3 dirToNode = (targetWorld - transform.position);
            float distToNode = dirToNode.magnitude;
            Vector3 moveDir = dirToNode.normalized;

            Vector3 repulsion = Vector3.zero;
            ChaserAI[] peers = FindObjectsByType<ChaserAI>(FindObjectsInactive.Exclude, FindObjectsSortMode.None);

            foreach (ChaserAI p in peers) {
                if (p != this) {
                    float d = Vector3.Distance(transform.position, p.transform.position);
                    // Se o colega estiver a menos de 1 metro de distância, empurram-se!
                    if (d < 1.0f && d > 0.01f) {
                        Vector3 push = transform.position - p.transform.position;
                        push.y = 0; // Ignora o eixo Y para não começarem a voar
                        repulsion += push.normalized * (1.0f - d);
                    }
                }
            }

            // 3. Mistura a vontade de ir para a frente com o empurrão lateral
            Vector3 finalDir = (moveDir + repulsion * 1.5f).normalized;

            // 4. Move o inimigo usando a nova direção aberta (em vez de forçar o MoveTowards cego)
            transform.position += finalDir * moveSpeed * Time.deltaTime;

            // 5. Roda o modelo 3D para olhar na direção do movimento
            if (finalDir != Vector3.zero) transform.forward = finalDir;

            // 6. Atualiza a posição na grelha (Aumentei a tolerância para 0.2f porque a repulsão pode fazê-los falhar o centro exato por milímetros)
            if (Vector3.Distance(new Vector3(transform.position.x, 0, transform.position.z),
                                new Vector3(targetWorld.x, 0, targetWorld.z)) < 0.2f) {
                gridPos = path[1];
            }
        }

        // Verifica colisão final com o jogador
        if (gridPos == GameManager.Instance.agent.gridPos) {
            GameManager.Instance.HandleDamage("Apanhado por Inimigo!");
            Destroy(gameObject); // O inimigo "explode" ao tocar no jogador
        }
    }
}