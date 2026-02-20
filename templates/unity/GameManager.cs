using UnityEngine;
using UnityEngine.SceneManagement;

public class GameManager : MonoBehaviour
{
    public static GameManager Instance;

    public float timeLimit = 10f;
    float timer;
    bool finished;

    void Awake()
    {
        Instance = this;
    }

    void Start()
    {
        timer = timeLimit;
    }

    void Update()
    {
        if (finished) return;

        timer -= Time.deltaTime;

        if (timer <= 0f)
        {
            Lose();
        }
    }

    public void Win()
    {
        if (finished) return;
        finished = true;
        Debug.Log("WIN!");
        Invoke(nameof(Restart), 2f);
    }

    void Lose()
    {
        if (finished) return;
        finished = true;
        Debug.Log("TIME UP!");
        Invoke(nameof(Restart), 2f);
    }

    void Restart()
    {
        SceneManager.LoadScene(SceneManager.GetActiveScene().name);
    }
}