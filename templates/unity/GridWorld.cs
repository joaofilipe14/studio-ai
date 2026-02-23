using System.Collections.Generic;
using UnityEngine;

public class GridWorld : MonoBehaviour
{
    public int Width { get; private set; }
    public int Height { get; private set; }
    public float cellSize { get; private set; }
    private bool[,] blocked;

    public void Build(int w, int h, float size, float fill, int seed)
    {
        Width = w; Height = h; cellSize = size;
        blocked = new bool[w, h];
        System.Random rng = new System.Random(seed);
        for (int x = 0; x < w; x++)
            for (int z = 0; z < h; z++)
                if (rng.NextDouble() < fill) blocked[x, z] = true;
    }

    public bool IsBlocked(Vector2Int p) => p.x < 0 || p.x >= Width || p.y < 0 || p.y >= Height || blocked[p.x, p.y];

    // Converte a coordenada da grelha para o mundo 3D (ajustado ao centro)
    public Vector3 GridToWorld(Vector2Int p, float y = 0.5f)
    {
        float offsetX = (Width * cellSize) / 2f;
        float offsetZ = (Height * cellSize) / 2f;
        return new Vector3(p.x * cellSize - offsetX + (cellSize / 2f), y, p.y * cellSize - offsetZ + (cellSize / 2f));
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
        for (int i = 0; i < 200; i++)
        {
            Vector2Int p = new Vector2Int(rng.Next(Width), rng.Next(Height));
            if (!IsBlocked(p)) return p;
        }
        return Vector2Int.zero;
    }
}