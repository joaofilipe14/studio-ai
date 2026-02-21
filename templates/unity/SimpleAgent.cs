using UnityEngine;
using UnityEngine.AI;

[RequireComponent(typeof(NavMeshAgent))]
public class SimpleAgent : MonoBehaviour
{
    [Header("Settings")]
    public Transform goal;
    public float stopDistance = 0.6f;

    [Header("Stuck Detection")]
    public float stuckSpeedEpsilon = 0.05f;
    public float stuckMaxTime = 2.0f;
    private float stuckTimer = 0f;

    private NavMeshAgent agent;
    private bool finished;
    private bool isUserControlled = false;

    void Awake()
    {
        agent = GetComponent<NavMeshAgent>();
        agent.stoppingDistance = stopDistance;
        agent.autoBraking = true;

        // Importante: Rigidbody precisa de ser Kinematic para não conflitar com NavMesh
        Rigidbody rb = GetComponent<Rigidbody>();
        if (rb != null) rb.isKinematic = true;
    }

    public void Configure(AgentData data, Transform currentGoal)
    {
        this.goal = currentGoal;
        this.stopDistance = data.stopDistance;
        this.isUserControlled = data.userControl;

        if (agent != null)
        {
            // O segredo: Mantemos o agent.enabled = true para usar o agent.Move(),
            // mas limpamos qualquer destino anterior.
            agent.enabled = true;
            agent.ResetPath();

            agent.speed = data.speed;
            agent.acceleration = data.acceleration;
            agent.stoppingDistance = stopDistance;
        }
    }

    void Update()
    {
        if (finished) return;

        if (isUserControlled)
        {
            HandleManualMovement();
        }
        else
        {
            HandleAIMovement();
        }
    }

    void HandleManualMovement()
    {
        float moveX = Input.GetAxis("Horizontal");
        float moveZ = Input.GetAxis("Vertical");

        Vector3 move = new Vector3(moveX, 0, moveZ).normalized;
        float speed = currentGenomeSpeed();

        if (agent != null && agent.isOnNavMesh)
        {
            // agent.Move respeita os obstáculos e paredes do NavMesh!
            agent.Move(move * speed * Time.deltaTime);

            if (move != Vector3.zero)
                transform.forward = move;
        }

        // Condição de vitória manual APENAS para modo PointToPoint
        if (GameManager.Instance != null && !GameManager.Instance.IsCollectMode())
        {
            if (goal != null && Vector3.Distance(transform.position, goal.position) <= stopDistance)
            {
                OnWin();
            }
        }
    }

    void HandleAIMovement()
    {
        if (goal == null || !agent.isOnNavMesh) return;

        agent.SetDestination(goal.position);

        if (!agent.pathPending && agent.remainingDistance <= agent.stoppingDistance)
        {
            if (!agent.hasPath || agent.velocity.sqrMagnitude == 0f)
            {
                OnWin();
                return;
            }
        }

        // Stuck Detection
        if (agent.velocity.magnitude < stuckSpeedEpsilon && agent.hasPath && !agent.pathPending)
            stuckTimer += Time.deltaTime;
        else
            stuckTimer = 0f;

        if (stuckTimer >= stuckMaxTime)
        {
            stuckTimer = 0f;
            if (GameManager.Instance != null) GameManager.Instance.NotifyStuck();
        }
    }

    public void OnWin()
    {
        if (finished) return;
        finished = true;

        if (agent.isActiveAndEnabled)
        {
            agent.isStopped = true;
            agent.ResetPath();
        }

        if (GameManager.Instance != null) GameManager.Instance.Win();
    }

    public void ResetAgent(Vector3 newPos, Transform newGoal)
    {
        finished = false;
        goal = newGoal;
        stuckTimer = 0f;

        if (agent != null)
        {
            agent.enabled = true;
            agent.Warp(newPos);
            agent.isStopped = false;
            agent.ResetPath();
        }
    }

    private float currentGenomeSpeed() => (agent != null) ? agent.speed : 5f;
}