using UnityEngine;

public class SimpleAgent : MonoBehaviour
{
    public Transform goal;
    public float speed = 3f;
    public float stopDistance = 0.5f;

    bool finished;

    void Update()
    {
        if (finished || goal == null) return;

        Vector3 toGoal = goal.position - transform.position;
        toGoal.y = 0f;

        if (toGoal.magnitude <= stopDistance)
        {
            OnWin();
            return;
        }

        Vector3 dir = toGoal.normalized;
        transform.position += dir * speed * Time.deltaTime;
        transform.forward = Vector3.Lerp(transform.forward, dir, 10f * Time.deltaTime);
    }

    public void OnWin()
    {
        if (finished) return;
        finished = true;
        Debug.Log("Agent finished!");
        GameManager.Instance.Win();
    }
}