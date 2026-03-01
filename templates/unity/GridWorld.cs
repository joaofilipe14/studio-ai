using UnityEngine;
using System.Collections.Generic;

public class GridWorld : MonoBehaviour
{
    public int Width { get; private set; }
    public int Height { get; private set; }
    public float CellSize { get; private set; }

    private bool[,] grid;

    public void Build(int width, int height, float cellSize, int obstacleCount, int seed)
    {
        Width = width;
        Height = height;
        CellSize = cellSize;
        grid = new bool[width, height];

        // 1. PAREDES EXTERIORES
        for (int x = 0; x < width; x++) {
            grid[x, 0] = true;
            grid[x, height - 1] = true;
        }
        for (int y = 0; y < height; y++) {
            grid[0, y] = true;
            grid[width - 1, y] = true;
        }

        // 2. GERADOR DE LABIRINTO INTERIOR
        System.Random rng = new System.Random(seed);
        int placed = 0;
        int attempts = 0;

        while (placed < obstacleCount && attempts < 10000)
        {
            attempts++;

            int rx = rng.Next(2, width - 2);
            int ry = rng.Next(2, height - 2);
            if (Mathf.Abs(rx - width/2) < 2 && Mathf.Abs(ry - height/2) < 2) continue;
            if (!grid[rx, ry])
            {
                int length = rng.Next(1, 5);
                bool horizontal = rng.Next(0, 2) == 0;

                for (int i = 0; i < length; i++) {
                    int nx = horizontal ? rx + i : rx;
                    int ny = horizontal ? ry : ry + i;

                    if (nx < width - 2 && ny < height - 2 && !grid[nx, ny]) {
                        grid[nx, ny] = true;
                        placed++;

                        if (placed >= obstacleCount) break;
                    }
                }
            }
        }
    }

    public bool IsBlocked(Vector2Int pos) {
        if (pos.x < 0 || pos.x >= Width || pos.y < 0 || pos.y >= Height) return true;
        return grid[pos.x, pos.y];
    }

    public Vector2Int WorldToGrid(Vector3 worldPos) {
        int x = Mathf.RoundToInt(worldPos.x / CellSize);
        int z = Mathf.RoundToInt(worldPos.z / CellSize);
        return new Vector2Int(x, z);
    }

    public Vector3 GridToWorld(Vector2Int gridPos, float yOffset = 0f) {
        return new Vector3(gridPos.x * CellSize, yOffset, gridPos.y * CellSize);
    }

    public Vector2Int RandomFreeCell(System.Random rng) {
        for (int i = 0; i < 2000; i++) {
            int x = rng.Next(1, Width - 1);
            int y = rng.Next(1, Height - 1);
            if (!grid[x, y]) return new Vector2Int(x, y);
        }
        return new Vector2Int(Width / 2, Height / 2);
    }

    // ========================================================
    // O CÉREBRO DE NAVEGAÇÃO DOS INIMIGOS (DE VOLTA!)
    // ========================================================
    public bool TryFindPath(Vector2Int start, Vector2Int target, List<Vector2Int> path)
    {
        path.Clear();
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

                if (next.x >= 0 && next.x < Width && next.y >= 0 && next.y < Height) {
                    if (!IsBlocked(next) && !cameFrom.ContainsKey(next)) {
                        queue.Enqueue(next);
                        cameFrom[next] = current;
                    }
                }
            }
        }

        if (!found) return false;

        Vector2Int curr = target;
        while (curr != start) {
            path.Add(curr);
            curr = cameFrom[curr];
        }
        path.Add(start);
        path.Reverse();
        return true;
    }
}