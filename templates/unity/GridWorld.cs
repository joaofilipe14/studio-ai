using System.Collections.Generic;
using UnityEngine;

public class GridWorld : MonoBehaviour
{
    public int Width { get; private set; }
    public int Height { get; private set; }
    public float CellSize { get; private set; }
    private bool[,] blocked;

    public void Build(int w, int h, float size, int obstacleCount, int seed)
    {
        Width = w;
        Height = h;
        CellSize = size;
        blocked = new bool[w, h];

        // 1. Preenche TUDO com paredes (Mapa sólido)
        for (int x = 0; x < w; x++)
            for (int y = 0; y < h; y++)
                blocked[x, y] = true;

        // 2. Calcula quantas células têm de ficar livres para andarmos
        int totalCells = w * h;
        int targetEmptyCells = totalCells - obstacleCount;
        if (targetEmptyCells < 1) targetEmptyCells = 1;

        // 3. O Algoritmo "Drunkard's Walk" para escavar corredores conectados
        System.Random rng = new System.Random(seed);
        int currentX = w / 2; // Começa no centro
        int currentY = h / 2;

        blocked[currentX, currentY] = false;
        int emptyCount = 1;

        // Direções (Cima, Baixo, Esquerda, Direita)
        int[] dx = { 0, 0, -1, 1 };
        int[] dy = { -1, 1, 0, 0 };

        while (emptyCount < targetEmptyCells)
        {
            // O mineiro escolhe uma direção aleatória
            int dir = rng.Next(0, 4);
            int nextX = currentX + dx[dir];
            int nextY = currentY + dy[dir];

            // Garante que o mineiro não sai dos limites do mapa
            if (nextX >= 0 && nextX < w && nextY >= 0 && nextY < h)
            {
                currentX = nextX;
                currentY = nextY;

                // Se for parede, escava!
                if (blocked[currentX, currentY])
                {
                    blocked[currentX, currentY] = false;
                    emptyCount++;
                }
            }
        }
    }

public bool IsBlocked(Vector2Int pos) {
        if (pos.x < 0 || pos.x >= Width || pos.y < 0 || pos.y >= Height) return true;
        return blocked[pos.x, pos.y];
    }
    // Converte a coordenada da grelha para o mundo 3D (ajustado ao centro)
    public Vector3 GridToWorld(Vector2Int gridPos, float yOffset = 0) {
        float x = (gridPos.x - Width / 2f) * CellSize + CellSize / 2f;
        float z = (gridPos.y - Height / 2f) * CellSize + CellSize / 2f;
        return new Vector3(x, yOffset, z);
    }

    public Vector2Int WorldToGrid(Vector3 worldPos) {
            int x = Mathf.FloorToInt((worldPos.x + Width * CellSize / 2f) / CellSize);
            int y = Mathf.FloorToInt((worldPos.z + Height * CellSize / 2f) / CellSize);
            return new Vector2Int(x, y);
        }

    // Algoritmo de procura de caminho (BFS) para a grelha
    public bool TryFindPath(Vector2Int start, Vector2Int goal, List<Vector2Int> outPath)
    {
        outPath.Clear();
        if (IsBlocked(start) || IsBlocked(goal)) return false;

        Queue<Vector2Int> queue = new Queue<Vector2Int>();
        Dictionary<Vector2Int, Vector2Int> cameFrom = new Dictionary<Vector2Int, Vector2Int>();
        queue.Enqueue(start);
        cameFrom[start] = start;

        while (queue.Count > 0)
        {
            Vector2Int current = queue.Dequeue();
            if (current == goal)
            {
                Vector2Int temp = goal;
                while (temp != start) { outPath.Add(temp); temp = cameFrom[temp]; }
                outPath.Add(start);
                outPath.Reverse();
                return true;
            }
            foreach (Vector2Int dir in new Vector2Int[] { Vector2Int.up, Vector2Int.down, Vector2Int.left, Vector2Int.right })
            {
                Vector2Int next = current + dir;
                if (!IsBlocked(next) && !cameFrom.ContainsKey(next))
                {
                    cameFrom[next] = current;
                    queue.Enqueue(next);
                }
            }
        }
        return false;
    }

    public Vector2Int RandomFreeCell(System.Random rng)
    {
        for (int i = 0; i < 1000; i++) {
            int x = rng.Next(0, Width);
            int y = rng.Next(0, Height);
            if (!blocked[x, y]) return new Vector2Int(x, y);
        }
        return new Vector2Int(Width / 2, Height / 2);
    }
}