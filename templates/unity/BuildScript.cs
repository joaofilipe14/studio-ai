#pragma warning disable 0618

using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.AI;
using System.IO;
using UnityEditor.Build.Reporting;

public static class BuildScript
{
    // --- FUNÇÃO NOVA VISUAL SEGURA ---
    static Material CreateColorMaterial(string name, Color color, bool glow = false)
    {
        Material mat = new Material(Shader.Find("Standard"));
        mat.color = color;
        if (glow)
        {
            mat.EnableKeyword("_EMISSION");
            mat.SetColor("_EmissionColor", color * 2.5f);
        }
        return mat;
    }

    static void EnsureTagsExist()
    {
        SerializedObject tagManager = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagManager.asset")[0]);
        SerializedProperty tagsProp = tagManager.FindProperty("tags");

        string[] tagsToEnsure = { "Collectible", "Player" };

        foreach (string tagName in tagsToEnsure)
        {
            bool found = false;
            for (int i = 0; i < tagsProp.arraySize; i++)
            {
                if (tagsProp.GetArrayElementAtIndex(i).stringValue == tagName)
                {
                    found = true;
                    break;
                }
            }

            if (!found)
            {
                tagsProp.InsertArrayElementAtIndex(tagsProp.arraySize);
                tagsProp.GetArrayElementAtIndex(tagsProp.arraySize - 1).stringValue = tagName;
            }
        }
        tagManager.ApplyModifiedProperties();
    }

    public static void MakeBuild()
    {
        EnsureTagsExist();

        if (!AssetDatabase.IsValidFolder("Assets/Scenes"))
        {
            AssetDatabase.CreateFolder("Assets", "Scenes");
        }
        Directory.CreateDirectory("Builds");

        string genomePath = Path.Combine(Directory.GetCurrentDirectory(), "game_genome.json");

        // CORREÇÃO AQUI: Lê a coleção inteira e usa a primeira configuração para criar o tamanho da Arena
        GameGenomeCollection allGenomes = GameGenomeCollection.Load(genomePath);
        GameGenome genome = (allGenomes != null && allGenomes.configs != null && allGenomes.configs.Length > 0)
                            ? allGenomes.configs[0]
                            : new GameGenome();
        genome.Validate();

        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        // --- MATERIAIS VISUAIS ---
        Material matFloor = CreateColorMaterial("FloorMat", new Color(0.1f, 0.1f, 0.15f));
        Material matWall = CreateColorMaterial("WallMat", new Color(0.2f, 0.2f, 0.3f));
        Material matAgent = CreateColorMaterial("AgentMat", Color.cyan, true);
        Material matGoal = CreateColorMaterial("GoalMat", Color.yellow, true);

        // Camera & Lights
        var camGO = new GameObject("Main Camera");
        var cam = camGO.AddComponent<Camera>();
        camGO.tag = "MainCamera";
        camGO.transform.position = new Vector3(0, 15f, -12f);
        camGO.transform.rotation = Quaternion.Euler(55f, 0f, 0f);
        cam.backgroundColor = new Color(0.05f, 0.05f, 0.1f);
        cam.clearFlags = CameraClearFlags.SolidColor;

        var lightGO = new GameObject("Directional Light");
        var light = lightGO.AddComponent<Light>();
        light.type = LightType.Directional;
        light.color = new Color(0.8f, 0.8f, 1f);
        light.intensity = 0.7f;
        lightGO.transform.rotation = Quaternion.Euler(50, -30, 0);

        // Floor
        var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Floor";
        float planeScale = (genome.arena.halfSize * 2f) / 10f;
        floor.transform.localScale = new Vector3(planeScale, 1f, planeScale);
        floor.transform.position = Vector3.zero;
        floor.GetComponent<Renderer>().material = matFloor;
        GameObjectUtility.SetStaticEditorFlags(floor, StaticEditorFlags.NavigationStatic);

        // Paredes
        if (genome.arena.walls)
        {
            float h = genome.arena.halfSize;
            CreateWall("Wall_N", new Vector3(0, 0.5f, h), new Vector3(h * 2f, 1f, 0.5f), matWall);
            CreateWall("Wall_S", new Vector3(0, 0.5f, -h), new Vector3(h * 2f, 1f, 0.5f), matWall);
            CreateWall("Wall_E", new Vector3(h, 0.5f, 0), new Vector3(0.5f, 1f, h * 2f), matWall);
            CreateWall("Wall_W", new Vector3(-h, 0.5f, 0), new Vector3(0.5f, 1f, h * 2f), matWall);
        }

        // GERAÇÃO DE OBSTÁCULOS
        Vector3 startPos = new Vector3(0, 1f, 0);
        Vector3 finalGoalPos = Vector3.zero;
        bool levelIsValid = false;

        for (int attempt = 0; attempt < 10; attempt++)
        {
            var oldObstacles = GameObject.FindObjectsOfType<GameObject>();
            foreach (var obj in oldObstacles) {
                if (obj.name.StartsWith("Obstacle_")) GameObject.DestroyImmediate(obj);
            }

            Random.InitState(genome.seed + attempt);

            for (int i = 0; i < genome.obstacles.count; i++)
            {
                var obs = GameObject.CreatePrimitive(PrimitiveType.Cube);
                obs.name = $"Obstacle_{i}";
                obs.transform.position = RandomPointFar(genome.arena.halfSize, startPos, 2.0f);
                float scaleY = Random.Range(genome.obstacles.minScale, genome.obstacles.maxScale);
                float scaleXZ = Random.Range(genome.obstacles.minScale, genome.obstacles.maxScale);
                obs.transform.localScale = new Vector3(scaleXZ, scaleY, scaleXZ);
                obs.GetComponent<Renderer>().material = matWall;
                GameObjectUtility.SetStaticEditorFlags(obs, StaticEditorFlags.NavigationStatic);
            }

            UnityEditor.AI.NavMeshBuilder.BuildNavMesh();
            Vector3 testGoalPos = RandomPointFar(genome.arena.halfSize, startPos, 4.0f);
            NavMeshPath path = new NavMeshPath();
            NavMesh.CalculatePath(startPos, testGoalPos, NavMesh.AllAreas, path);

            if (path.status == NavMeshPathStatus.PathComplete) {
                levelIsValid = true;
                finalGoalPos = testGoalPos;
                break;
            }
        }

        // CORREÇÃO DO AVISO AQUI: Usa a variável no final
        if (!levelIsValid) {
            Debug.LogWarning("[BuildScript] Aviso: Caminho perfeito não encontrado. A usar o último gerado.");
        }

        // AGENTE
        var agentGO = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        agentGO.name = "Agent";
        agentGO.tag = "Player";
        agentGO.transform.position = startPos;
        agentGO.GetComponent<Renderer>().material = matAgent;

        var trail = agentGO.AddComponent<TrailRenderer>();
        trail.time = 0.5f;
        trail.startWidth = 0.5f;
        trail.endWidth = 0f;
        trail.material = new Material(Shader.Find("Sprites/Default"));
        trail.startColor = Color.cyan;
        trail.endColor = new Color(0, 1, 1, 0);

        var rb = agentGO.AddComponent<Rigidbody>();
        rb.isKinematic = true;
        rb.interpolation = RigidbodyInterpolation.Interpolate;

        var navAgent = agentGO.AddComponent<NavMeshAgent>();
        navAgent.speed = genome.agent.speed;
        navAgent.acceleration = genome.agent.acceleration;

        var agentScript = agentGO.AddComponent<SimpleAgent>();
        agentScript.stopDistance = genome.agent.stopDistance;

        // Goal
        var goalGO = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        goalGO.name = "Goal";
        goalGO.transform.localScale = Vector3.one * 0.8f;
        goalGO.transform.position = finalGoalPos;
        goalGO.GetComponent<Renderer>().material = matGoal;
        var goalCol = goalGO.GetComponent<Collider>();
        goalCol.isTrigger = true;
        goalGO.AddComponent<Goal>();

        // GameManager
        var gmGO = new GameObject("GameManager");
        var gm = gmGO.AddComponent<GameManager>();
        gm.agent = agentScript;
        gm.goal = goalGO.transform;

        agentScript.goal = goalGO.transform;

        EditorSceneManager.SaveScene(scene, "Assets/Scenes/Main.unity");
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene("Assets/Scenes/Main.unity", true) };

        var exePath = Path.Combine("Builds", "Game001.exe");
        BuildReport report = BuildPipeline.BuildPlayer(
            new[] { "Assets/Scenes/Main.unity" },
            exePath,
            BuildTarget.StandaloneWindows64,
            BuildOptions.None
        );

        if (report.summary.result == BuildResult.Succeeded)
        {
            string destGenome = Path.Combine("Builds", "game_genome.json");
            File.Copy(genomePath, destGenome, true);
        }

        EditorApplication.Exit(report.summary.result == BuildResult.Succeeded ? 0 : 1);
    }

    static Vector3 RandomPointFar(float halfSize, Vector3 awayFrom, float minDistance)
    {
        for (int i = 0; i < 60; i++)
        {
            float x = Random.Range(-halfSize + 1.5f, halfSize - 1.5f);
            float z = Random.Range(-halfSize + 1.5f, halfSize - 1.5f);
            var p = new Vector3(x, 0.5f, z);
            if (Vector3.Distance(p, awayFrom) >= minDistance) return p;
        }
        return new Vector3(halfSize * 0.6f, 0.5f, halfSize * 0.6f);
    }

    static void CreateWall(string name, Vector3 pos, Vector3 size, Material mat)
    {
        var w = GameObject.CreatePrimitive(PrimitiveType.Cube);
        w.name = name;
        w.transform.position = pos;
        w.transform.localScale = size;
        w.GetComponent<Renderer>().material = mat;
        GameObjectUtility.SetStaticEditorFlags(w, StaticEditorFlags.NavigationStatic);
    }
}