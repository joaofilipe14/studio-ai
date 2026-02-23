using UnityEngine;
using System.Collections.Generic;

public class ChaserAI : MonoBehaviour
{
    public GridWorld world;
    public Vector2Int gridPos;
    public float moveSpeed = 3.5f;
    private List<Vector2Int> path = new List<Vector2Int>();

    void Update()
    {
        // Se o jogo terminou ou as referências faltarem, o perseguidor para
        if (world == null || GameManager.Instance == null || GameManager.Instance.agent == null || GameManager.Instance.finished)
            return;

        // O objetivo do Chaser é a posição atual do Agente (SimpleAgent)
        Vector2Int targetPos = GameManager.Instance.agent.gridPos;

        // Tenta encontrar o caminho até ao jogador através da grelha
        if (world.TryFindPath(gridPos, targetPos, path) && path.Count > 1)
        {
            // Move-se para a próxima célula (índice 1)
            Vector3 targetWorld = world.GridToWorld(path[1], transform.position.y);
            transform.position = Vector3.MoveTowards(transform.position, targetWorld, moveSpeed * Time.deltaTime);

            // Rotação suave para olhar para o jogador
            Vector3 lookDir = (targetWorld - transform.position).normalized;
            if (lookDir != Vector3.zero) transform.forward = lookDir;

            // Atualiza a posição lógica na grelha ao chegar ao destino
            if (Vector3.Distance(new Vector3(transform.position.x, 0, transform.position.z),
                                new Vector3(targetWorld.x, 0, targetWorld.z)) < 0.1f)
            {
                gridPos = path[1];
            }
        }

        // Se o Chaser atingir a mesma célula do Agente, conta como captura
        if (gridPos == GameManager.Instance.agent.gridPos)
        {
            GameManager.Instance.OnAgentCaught();
        }
    }
}