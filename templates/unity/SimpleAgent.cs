using UnityEngine;
using System.Collections.Generic;

public class SimpleAgent : MonoBehaviour {
    public GridWorld world;
    public Vector2Int gridPos;
    public float moveSpeed = 5f;
    // Posição alvo para o movimento suave
    private Vector3 targetWorldPos;
    // Memória do Bot (IA)
    private List<Vector2Int> currentPath;
    private int pathIndex = 0;
    private float pathRecalculateTimer = 0f;

    void Start() {
        targetWorldPos = world.GridToWorld(gridPos, transform.position.y);
    }

    void Update() {
        if (GameManager.Instance == null || GameManager.Instance.finished || Time.timeScale == 0) return;
        // Se o controlo for do jogador, chama o movimento manual. Senão, usa a IA.
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

                // Prevenção de segurança para não sair do mapa
                if (nextPos.x >= 0 && nextPos.x < world.Width && nextPos.y >= 0 && nextPos.y < world.Height) {
                    if (!world.IsBlocked(nextPos)) {
                        gridPos = nextPos; // Atualiza a posição alvo na grelha
                        targetWorldPos = world.GridToWorld(gridPos, transform.position.y);
                    }
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

    // ==========================================
    // 2. CÉREBRO DO BOT (PATHFINDING BFS JUSTO)
    // ==========================================
    void HandleBotAI() {
        // Move visualmente o agente
        transform.position = Vector3.MoveTowards(transform.position, targetWorldPos, moveSpeed * Time.deltaTime);

        // Roda o agente suavemente
        Vector3 dir = (targetWorldPos - transform.position).normalized;
        if (dir != Vector3.zero) {
            transform.forward = Vector3.Lerp(transform.forward, dir, Time.deltaTime * 15f);
        }

        // Só toma decisões lógicas se já chegou fisicamente ao centro da célula
        if (Vector3.Distance(transform.position, targetWorldPos) >= 0.05f) return;

        gridPos = world.WorldToGrid(transform.position);
        pathRecalculateTimer -= Time.deltaTime;

        // Recalcula a rota a cada 0.5s ou se esgotou os passos
        if (currentPath == null || pathIndex >= currentPath.Count || pathRecalculateTimer <= 0) {
            RecalculatePath();
            pathRecalculateTimer = 0.5f;
        }

        // Dá a ordem para avançar para a próxima célula do caminho
        if (currentPath != null && pathIndex < currentPath.Count) {
            Vector2Int nextPos = currentPath[pathIndex];
            targetWorldPos = world.GridToWorld(nextPos, transform.position.y);
            pathIndex++;
        }
    }

    void RecalculatePath() {
        Vector2Int targetPos = gridPos;

        // 1. Descobrir em que nível estamos para definir a "Ganância"
        int currentLvl = GameManager.Instance.currentLevel != null ? GameManager.Instance.currentLevel.level_id : 1;

        // 2. Calcular a Quota: Quantas moedas o Bot vai tentar apanhar antes de fugir?
        float greedPercentage = 1.0f; // Níveis 1 e 2: Tenta apanhar 100% das moedas

        if (currentLvl >= 8) greedPercentage = 0.25f;      // Níveis 8-10: Muito perigoso, só apanha 25%
        else if (currentLvl >= 5) greedPercentage = 0.50f; // Níveis 5-7: Risco moderado, apanha 50%
        else if (currentLvl >= 3) greedPercentage = 0.75f; // Níveis 3-4: Apanha 75%

        int targetCoins = Mathf.RoundToInt(GameManager.Instance.collectibles * greedPercentage);

        GameObjective[] objectives = Object.FindObjectsByType<GameObjective>(FindObjectsSortMode.None);
        bool seekingCoin = false;

        // 3. DECISÃO: Ainda lhe faltam moedas para atingir a quota?
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

        // 4. DECISÃO: Se já atingiu a quota, ou se não sobraram moedas... FOGE PARA O PORTAL!
        if (!seekingCoin) {
            foreach (var obj in objectives) {
                if (obj.type == ObjectiveType.ExitPortal) {
                    targetPos = obj.gridPos;
                    break;
                }
            }
        }

        // Calcular a Rota usando BFS
        currentPath = FindPathBFS(gridPos, targetPos);
        pathIndex = 0;

        if (currentPath != null && currentPath.Count > 1) {
            pathIndex = 1;
        }
    }

    // Algoritmo de mapeamento limpo (Espalha-se em cruz ignorando as paredes)
    List<Vector2Int> FindPathBFS(Vector2Int start, Vector2Int target) {
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

                // Respeita estritamente os limites do mapa e a colisão com as paredes!
                if (next.x >= 0 && next.x < world.Width && next.y >= 0 && next.y < world.Height) {
                    if (!world.IsBlocked(next) && !cameFrom.ContainsKey(next)) {
                        queue.Enqueue(next);
                        cameFrom[next] = current;
                    }
                }
            }
        }

        if (!found) return null; // Não há caminho (o alvo está trancado pelas paredes da IA)

        // Desfazer o caminho de trás para a frente
        List<Vector2Int> path = new List<Vector2Int>();
        Vector2Int curr = target;
        while (curr != start) {
            path.Add(curr);
            curr = cameFrom[curr];
        }
        path.Add(start);
        path.Reverse(); // Inverter para a ordem correta
        return path;
    }

    public void ResetPosition(Vector2Int newPos) {
        gridPos = newPos;
        targetWorldPos = world.GridToWorld(gridPos, transform.position.y);
        transform.position = targetWorldPos;

        // Limpa a memória do caminho antigo
        currentPath = null;
        pathIndex = 0;
        pathRecalculateTimer = 0f;
    }
}