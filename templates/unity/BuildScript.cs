using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using System.IO;

public static class BuildScript
{
    public static void MakeBuild()
    {
        Directory.CreateDirectory("Assets/Scenes");
        Directory.CreateDirectory("Builds");

        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        // =========================
        // CAMERA
        // =========================
        var camGO = new GameObject("Main Camera");
        var cam = camGO.AddComponent<Camera>();
        camGO.tag = "MainCamera";
        camGO.transform.position = new Vector3(0, 6f, -10f);
        camGO.transform.LookAt(Vector3.zero);

        // =========================
        // LIGHT
        // =========================
        var lightGO = new GameObject("Directional Light");
        var light = lightGO.AddComponent<Light>();
        light.type = LightType.Directional;
        lightGO.transform.rotation = Quaternion.Euler(50, -30, 0);

        // =========================
        // GROUND
        // =========================
        var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
        ground.name = "Ground";
        ground.transform.position = Vector3.zero;
        ground.transform.localScale = new Vector3(2f, 1f, 2f);

        // =========================
        // GOAL
        // =========================
        float arenaSize = 8f;
        Vector3 randomPos = new Vector3(
            Random.Range(-arenaSize, arenaSize),
            0.5f,
            Random.Range(-arenaSize, arenaSize)
        );

        var goal = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        goal.name = "Goal";
        goal.transform.position = randomPos;
        goal.transform.localScale = Vector3.one;

        var goalCollider = goal.GetComponent<SphereCollider>();
        goalCollider.isTrigger = true;

        goal.AddComponent<Goal>();

        goal.GetComponent<Renderer>().sharedMaterial.color = Color.green;

        // =========================
        // AGENT
        // =========================
        var agent = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        agent.name = "Agent";
        agent.transform.position = new Vector3(-4f, 1f, -4f);

        var rb = agent.AddComponent<Rigidbody>();
        rb.constraints = RigidbodyConstraints.FreezeRotationX |
                         RigidbodyConstraints.FreezeRotationZ;

        var simpleAgent = agent.AddComponent<SimpleAgent>();
        simpleAgent.goal = goal.transform;

        var agentRenderer = agent.GetComponent<Renderer>();
        agentRenderer.sharedMaterial.color = Color.blue;

        var gm = new GameObject("GameManager");
        gm.AddComponent<GameManager>();

        // =========================
        // SAVE SCENE
        // =========================
        EditorSceneManager.SaveScene(scene, "Assets/Scenes/Main.unity");

        EditorBuildSettings.scenes = new[]
        {
            new EditorBuildSettingsScene("Assets/Scenes/Main.unity", true)
        };

        // =========================
        // BUILD
        // =========================
        var exePath = Path.Combine("Builds", "Game001.exe");
        var report = BuildPipeline.BuildPlayer(
            new[] { "Assets/Scenes/Main.unity" },
            exePath,
            BuildTarget.StandaloneWindows64,
            BuildOptions.None
        );

        EditorApplication.Exit(report.summary.result ==
            UnityEditor.Build.Reporting.BuildResult.Succeeded ? 0 : 1);
    }
}