using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using System.IO;

public static class BuildScript
{
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
        Directory.CreateDirectory("Assets/Scenes");
        Directory.CreateDirectory("Builds");

        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        // Camera
        var camGO = new GameObject("Main Camera");
        var cam = camGO.AddComponent<Camera>();
        camGO.tag = "MainCamera";
        camGO.transform.position = new Vector3(0, 16f, -18f);
        camGO.transform.rotation = Quaternion.Euler(45f, 0f, 0f);

        // Light
        var lightGO = new GameObject("Directional Light");
        var light = lightGO.AddComponent<Light>();
        light.type = LightType.Directional;
        lightGO.transform.rotation = Quaternion.Euler(50, -30, 0);

        // GameManager
        var gmGO = new GameObject("GameManager");
        var gm = gmGO.AddComponent<GameManager>();

        // CONFIG base (muda aqui se quiseres)
        gm.gridWidth = 17;
        gm.gridHeight = 17;
        gm.cellSize = 1.0f;

        gm.seed = (int)System.DateTime.UtcNow.Ticks; // random por build
        gm.obstacles = 28;
        gm.collectibles = 5;
        gm.buildBorderWalls = true;

        gm.timeLimit = 25f;
        gm.rounds = 5;

        gm.agentMoveSpeed = 4.5f;
        gm.userControl = false;

        gm.spawnChaser = true;
        gm.chaserMoveSpeed = 3.5f;

        // Save scene
        EditorSceneManager.SaveScene(scene, "Assets/Scenes/Main.unity");

        // Build settings
        EditorBuildSettings.scenes = new[]
        {
            new EditorBuildSettingsScene("Assets/Scenes/Main.unity", true)
        };

        // Build
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