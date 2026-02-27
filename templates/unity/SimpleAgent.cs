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

            // 1. Ler o input puro (eixos do teclado)
            float h = 0; float v = 0;
            if (Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow)) v = 1;
            if (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow)) v = -1;
            if (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow)) h = 1;
            if (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow)) h = -1;

            if (h != 0 || v != 0) {
                // 2. Descobrir para onde a câmara olha no mundo 3D (ignorando o eixo Y/Céu)
                Transform camT = Camera.main.transform;
                Vector3 camForward = camT.forward;
                Vector3 camRight = camT.right;
                camForward.y = 0; camRight.y = 0;
                camForward.Normalize(); camRight.Normalize();

                // 3. Calcular a direção mundial pretendida com base no input
                Vector3 desiredWorldDir = (camForward * v + camRight * h).normalized;

                // 4. Mapear a direção mundial livre para a direção EXATA da Grelha
                // (Up = +Z, Down = -Z, Right = +X, Left = -X)
                Vector2Int bestGridDir = Vector2Int.zero;
                float maxDot = -Mathf.Infinity;

                Vector2Int[] gridDirs = { Vector2Int.up, Vector2Int.down, Vector2Int.left, Vector2Int.right };
                Vector3[] worldDirs = { Vector3.forward, Vector3.back, Vector3.left, Vector3.right };

                for (int i = 0; i < 4; i++) {
                    // O Dot Product diz-nos qual direção da grelha está mais alinhada com a direção desejada
                    float dot = Vector3.Dot(desiredWorldDir, worldDirs[i]);
                    if (dot > maxDot) {
                        maxDot = dot;
                        bestGridDir = gridDirs[i];
                    }
                }

                // 5. Aplicar o movimento na grelha se não houver parede
                Vector2Int nextPos = gridPos + bestGridDir;
                if (!world.IsBlocked(nextPos)) {
                    gridPos = nextPos; // Atualiza a posição alvo na grelha
                    targetWorldPos = world.GridToWorld(gridPos, transform.position.y);
                }
            }
        }

        // Move visualmente o agente para a posição lógica atual (targetWorldPos)
        transform.position = Vector3.MoveTowards(transform.position, targetWorldPos, moveSpeed * Time.deltaTime);

        // Roda o agente suavemente para a direção que se está a mover
        Vector3 dir = (targetWorldPos - transform.position).normalized;
        if (dir != Vector3.zero) {
            transform.forward = Vector3.Lerp(transform.forward, dir, Time.deltaTime * 15f);
        }
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