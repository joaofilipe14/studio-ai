using UnityEngine;

public class Goal : MonoBehaviour
{
    private void OnTriggerEnter(Collider other)
    {
        var agent = other.GetComponent<SimpleAgent>();
        if (agent != null)
        {
            Debug.Log("WIN: agent reached the goal!");
            agent.OnWin();
        }
    }
}