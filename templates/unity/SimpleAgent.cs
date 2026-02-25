using UnityEngine;
using System.Collections.Generic;

public class SimpleAgent : MonoBehaviour
{
    public GridWorld world;
    public Vector2Int gridPos;
    public float moveSpeed = 5f;
    private List<Vector2Int> path = new List<Vector2Int>();

    void Update() {
        if (GameManager.Instance == null || GameManager.Instance.finished) return;

        // Se o controlo for do jogador, chama o movimento manual. Senão, usa a IA.
        if (GameManager.Instance.userControl) {
            HandleManualMovement();
        } else {
            HandleAIMovement();
        }
    }

    void HandleManualMovement() {
        Vector3 targetWorldPos = world.GridToWorld(gridPos, transform.position.y);

        // O jogador só pode decidir a próxima direção quando o agente chegar ao centro do bloco atual
        if (Vector3.Distance(transform.position, targetWorldPos) < 0.05f) {
            Vector2Int inputDir = Vector2Int.zero;

            // Lê as teclas WASD ou as Setas do teclado
            if (Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow)) inputDir = Vector2Int.up;
            else if (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow)) inputDir = Vector2Int.down;
            else if (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow)) inputDir = Vector2Int.left;
            else if (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow)) inputDir = Vector2Int.right;

            // Se o jogador pressionou uma tecla, verifica se a próxima célula não é parede
            if (inputDir != Vector2Int.zero) {
                Vector2Int nextPos = gridPos + inputDir;
                if (!world.IsBlocked(nextPos)) {
                    gridPos = nextPos; // Atualiza a posição alvo na grelha
                    targetWorldPos = world.GridToWorld(gridPos, transform.position.y);
                }
            }
        }

        // Move visualmente o agente para a posição lógica atual (targetWorldPos)
        transform.position = Vector3.MoveTowards(transform.position, targetWorldPos, moveSpeed * Time.deltaTime);

        // Roda o agente para a direção que se está a mover
        Vector3 dir = (targetWorldPos - transform.position).normalized;
        if (dir != Vector3.zero) transform.forward = dir;
    }

    void HandleAIMovement() {
        Vector2Int? targetPos = null;
        if (GameManager.Instance.currentMode == "PointToPoint") {
            Goal goal = Object.FindFirstObjectByType<Goal>();
            if (goal != null) targetPos = goal.gridPos;
        } else {
            Collectible[] coins = Object.FindObjectsByType<Collectible>(FindObjectsSortMode.None);
            if (coins.Length > 0) {
                float minDist = float.MaxValue;
                foreach (var c in coins) {
                    float dist = Vector2Int.Distance(gridPos, c.gridPos);
                    if (dist < minDist) {
                        minDist = dist;
                        targetPos = c.gridPos;
                    }
                }
            }
        }

        if (targetPos.HasValue) {
            if (world.TryFindPath(gridPos, targetPos.Value, path) && path.Count > 1) {
                Vector3 targetWorld = world.GridToWorld(path[1], transform.position.y);
                transform.position = Vector3.MoveTowards(transform.position, targetWorld, moveSpeed * Time.deltaTime);

                Vector3 dir = (targetWorld - transform.position).normalized;
                if (dir != Vector3.zero) transform.forward = dir;

                if (Vector3.Distance(new Vector3(transform.position.x, 0, transform.position.z),
                                     new Vector3(targetWorld.x, 0, targetWorld.z)) < 0.1f)
                {
                    gridPos = path[1];
                }
            }
        }
    }
}