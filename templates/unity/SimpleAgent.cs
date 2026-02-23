using UnityEngine;
using System.Collections.Generic;

public class SimpleAgent : MonoBehaviour
{
    public GridWorld world;
    public Vector2Int gridPos;
    public float moveSpeed = 5f;
    private List<Vector2Int> path = new List<Vector2Int>();

    void Update()
    {
        if (GameManager.Instance == null || GameManager.Instance.finished) return;

        GameObject target = GameObject.FindWithTag("Collectible");
        if (target != null)
        {
            Vector2Int goal = target.GetComponent<Collectible>().gridPos;
            if (world.TryFindPath(gridPos, goal, path) && path.Count > 1)
            {
                Vector3 targetPos = world.GridToWorld(path[1]);
                transform.position = Vector3.MoveTowards(transform.position, targetPos, moveSpeed * Time.deltaTime);

                if (Vector3.Distance(transform.position, targetPos) < 0.05f)
                {
                    gridPos = path[1];
                }
            }
        }
    }
}