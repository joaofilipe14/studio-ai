using UnityEngine;
using System.Collections.Generic;

public class SimpleAgent : MonoBehaviour {
    public GridWorld world;
    public Vector2Int gridPos;
    public float moveSpeed = 5f;
    private Vector3 targetWorldPos;
    private List<Vector2Int> currentPath;
    private int pathIndex = 0;
    private float pathRecalculateTimer = 0f;

    void Start() {
        targetWorldPos = world.GridToWorld(gridPos, transform.position.y);
    }

    void Update() {
        if (GameManager.Instance == null || GameManager.Instance.finished || Time.timeScale == 0) return;
        if (GameManager.Instance.userControl) {
            HandleManualMovement();
        } else {
            HandleBotAI();
        }
    }

    // ==========================================
    // 1. CONTROLO HUMANO (Com a tua lógica de Câmara!)
    // ==========================================
    void HandleManualMovement() {
        if (Vector3.Distance(transform.position, targetWorldPos) < 0.05f) {
            float h = 0; float v = 0;
            if (Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow)) v = 1;
            if (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow)) v = -1;
            if (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow)) h = 1;
            if (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow)) h = -1;

            if (h != 0 || v != 0) {
                Transform camT = Camera.main.transform;
                Vector3 camForward = camT.forward;
                Vector3 camRight = camT.right;
                camForward.y = 0; camRight.y = 0;
                camForward.Normalize(); camRight.Normalize();
                Vector3 desiredWorldDir = (camForward * v + camRight * h).normalized;
                Vector2Int bestGridDir = Vector2Int.zero;
                float maxDot = -Mathf.Infinity;
                Vector2Int[] gridDirs = { Vector2Int.up, Vector2Int.down, Vector2Int.left, Vector2Int.right };
                Vector3[] worldDirs = { Vector3.forward, Vector3.back, Vector3.left, Vector3.right };

                for (int i = 0; i < 4; i++) {
                    float dot = Vector3.Dot(desiredWorldDir, worldDirs[i]);
                    if (dot > maxDot) {
                        maxDot = dot;
                        bestGridDir = gridDirs[i];
                    }
                }
                Vector2Int nextPos = gridPos + bestGridDir;
                if (nextPos.x >= 0 && nextPos.x < world.Width && nextPos.y >= 0 && nextPos.y < world.Height) {
                    if (!world.IsBlocked(nextPos)) {
                        gridPos = nextPos; // Atualiza a posição alvo na grelha
                        targetWorldPos = world.GridToWorld(gridPos, transform.position.y);
                    }
                }
            }
        }
        transform.position = Vector3.MoveTowards(transform.position, targetWorldPos, moveSpeed * Time.deltaTime);
        Vector3 dir = (targetWorldPos - transform.position).normalized;
        if (dir != Vector3.zero) {
            transform.forward = Vector3.Lerp(transform.forward, dir, Time.deltaTime * 15f);
        }
    }

    void HandleBotAI() {
        transform.position = Vector3.MoveTowards(transform.position, targetWorldPos, moveSpeed * Time.deltaTime);
        Vector3 dir = (targetWorldPos - transform.position).normalized;
        if (dir != Vector3.zero) {
            transform.forward = Vector3.Lerp(transform.forward, dir, Time.deltaTime * 30f);
        }
        if (Vector3.Distance(transform.position, targetWorldPos) >= 0.15f) return;
        gridPos = world.WorldToGrid(transform.position);
        pathRecalculateTimer -= Time.deltaTime;
        if (currentPath == null || pathIndex >= currentPath.Count || pathRecalculateTimer <= 0) {
            RecalculatePath();
            pathRecalculateTimer = 0.2f;
        }

        if (currentPath != null && pathIndex < currentPath.Count) {
            Vector2Int nextPos = currentPath[pathIndex];
            targetWorldPos = world.GridToWorld(nextPos, transform.position.y);
            pathIndex++;
        }
    }

    void RecalculatePath() {
        Vector2Int targetPos = gridPos;
        GameObjective[] objectives = Object.FindObjectsByType<GameObjective>(FindObjectsSortMode.None);
        ChaserAI[] enemies = FindObjectsByType<ChaserAI>(FindObjectsSortMode.None);

        // 🚨 1. INSTINTO DE FUGA: Se houver um inimigo muito perto, PRIORIDADE TOTAL À SAÍDA!
        bool dangerClose = false;
        foreach (var enemy in enemies) {
            if (Vector2Int.Distance(gridPos, enemy.gridPos) < 4f) {
                dangerClose = true;
                break;
            }
        }

        bool seekingCoin = false;

        if (dangerClose) {
            // FOGE! Procura logo o Portal de Saída
            foreach (var obj in objectives) {
                if (obj.type == ObjectiveType.ExitPortal) {
                    targetPos = obj.gridPos;
                    break;
                }
            }
        } else {
            // 2. Lógica normal de moedas (se não houver perigo imediato)
            int currentLvl = GameManager.Instance.currentLevel != null ? GameManager.Instance.currentLevel.level_id : 1;
            float greedPercentage = 1.0f;
            if (currentLvl >= 8) greedPercentage = 0.25f;
            else if (currentLvl >= 5) greedPercentage = 0.50f;
            else if (currentLvl >= 3) greedPercentage = 0.75f;

            int targetCoins = Mathf.RoundToInt(GameManager.Instance.collectibles * greedPercentage);

            if (GameManager.Instance.collectedInRound < targetCoins) {
                float minDist = float.MaxValue;
                foreach (var obj in objectives) {
                    if (obj.type == ObjectiveType.Coin) {
                        float d = Vector2Int.Distance(gridPos, obj.gridPos);
                        if (d < minDist) {
                            minDist = d;
                            targetPos = obj.gridPos;
                            seekingCoin = true;
                        }
                    }
                }
            }

            if (!seekingCoin) {
                foreach (var obj in objectives) {
                    if (obj.type == ObjectiveType.ExitPortal) {
                        targetPos = obj.gridPos;
                        break;
                    }
                }
            }
        }

        currentPath = FindPathBFS(gridPos, targetPos);
        pathIndex = 0;
        if (currentPath != null && currentPath.Count > 1) pathIndex = 1;
    }

    // Algoritmo que tenta rota segura primeiro, e rota suicida em último caso
    List<Vector2Int> FindPathBFS(Vector2Int start, Vector2Int target) {
        HashSet<Vector2Int> dangerZones = new HashSet<Vector2Int>();
        ChaserAI[] enemies = FindObjectsByType<ChaserAI>(FindObjectsSortMode.None);

        foreach (ChaserAI enemy in enemies) {
            dangerZones.Add(enemy.gridPos);
            dangerZones.Add(enemy.gridPos + Vector2Int.up);
            dangerZones.Add(enemy.gridPos + Vector2Int.down);
            dangerZones.Add(enemy.gridPos + Vector2Int.left);
            dangerZones.Add(enemy.gridPos + Vector2Int.right);
        }

        // 1. Tenta a rota segura (Onde o radar dos inimigos está ativo)
        List<Vector2Int> safePath = RunBFS(start, target, dangerZones, false);

        if (safePath != null && safePath.Count > 0) {
            return safePath;
        }

        // 2. Tenta a rota de desespero! (Ignora os inimigos porque está encurralado)
        return RunBFS(start, target, dangerZones, true);
    }

    // O Motor de Busca de Caminhos Duplo
    List<Vector2Int> RunBFS(Vector2Int start, Vector2Int target, HashSet<Vector2Int> dangerZones, bool ignoreDanger) {
        Queue<Vector2Int> queue = new Queue<Vector2Int>();
        Dictionary<Vector2Int, Vector2Int> cameFrom = new Dictionary<Vector2Int, Vector2Int>();

        queue.Enqueue(start);
        cameFrom[start] = start;

        Vector2Int[] dirs = { Vector2Int.up, Vector2Int.down, Vector2Int.left, Vector2Int.right };
        bool found = false;

        while (queue.Count > 0) {
            Vector2Int current = queue.Dequeue();
            if (current == target) {
                found = true;
                break;
            }

            foreach (Vector2Int dir in dirs) {
                Vector2Int next = current + dir;
                if (next.x >= 0 && next.x < world.Width && next.y >= 0 && next.y < world.Height) {
                    bool isDangerous = false;
                    if (!ignoreDanger && next != target) {
                         isDangerous = dangerZones.Contains(next);
                    }
                    if (!world.IsBlocked(next) && !cameFrom.ContainsKey(next) && !isDangerous) {
                        queue.Enqueue(next);
                        cameFrom[next] = current;
                    }
                }
            }
        }

        if (!found) return null; // Sem caminho físico possível (fechado por paredes reais)

        List<Vector2Int> path = new List<Vector2Int>();
        Vector2Int curr = target;
        while (curr != start) {
            path.Add(curr);
            curr = cameFrom[curr];
        }
        path.Add(start);
        path.Reverse();
        return path;
    }

    public void ResetPosition(Vector2Int newPos) {
        gridPos = newPos;
        targetWorldPos = world.GridToWorld(gridPos, transform.position.y);
        transform.position = targetWorldPos;
        currentPath = null;
        pathIndex = 0;
        pathRecalculateTimer = 0f;
    }
}