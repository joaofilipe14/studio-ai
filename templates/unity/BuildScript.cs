using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements; // 🚨 Adicionado para PanelSettings
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;
using UnityEditor.Build.Reporting;
using System.IO;

public class BuildScript {
    static void EnsureTagsExist() {
        SerializedObject tagManager = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagManager.asset")[0]);
        SerializedProperty tagsProp = tagManager.FindProperty("tags");
        string[] tagsToEnsure = { "Collectible", "Player" };
        foreach (string tagName in tagsToEnsure) {
            bool found = false;
            for (int i = 0; i < tagsProp.arraySize; i++) {
                if (tagsProp.GetArrayElementAtIndex(i).stringValue == tagName) { found = true; break; }
            }
            if (!found) {
                tagsProp.InsertArrayElementAtIndex(tagsProp.arraySize);
                tagsProp.GetArrayElementAtIndex(tagsProp.arraySize - 1).stringValue = tagName;
            }
        }
        tagManager.ApplyModifiedProperties();
    }

    public static void MakeBuild() {
        EnsureTagsExist();
        string uiDir = "Assets/Resources/UI";
        if (!Directory.Exists(uiDir)) Directory.CreateDirectory(uiDir);
        string panelPath = uiDir + "/DefaultPanelSettings.asset";

        if (!File.Exists(panelPath)) {
            PanelSettings newPanelSettings = ScriptableObject.CreateInstance<PanelSettings>();
            AssetDatabase.CreateAsset(newPanelSettings, panelPath);
            AssetDatabase.SaveAssets();
            Debug.Log("[BuildScript] PanelSettings criado dinamicamente em: " + panelPath);
        }

        Scene newScene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        GameObject uiObj = new GameObject("UI_Toolkit_Root");
        UIDocument doc = uiObj.AddComponent<UIDocument>();
        doc.panelSettings = AssetDatabase.LoadAssetAtPath<PanelSettings>(panelPath);

        GameObject camObj = new GameObject("Main Camera");
        camObj.tag = "MainCamera";
        Camera cam = camObj.AddComponent<Camera>();
        cam.transform.position = new Vector3(0, 15, -10);
        cam.transform.rotation = Quaternion.Euler(60, 0, 0);
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.02f, 0.02f, 0.05f);

        GameObject lightObj = new GameObject("Directional Light");
        Light light = lightObj.AddComponent<Light>();
        light.type = LightType.Directional;
        light.transform.rotation = Quaternion.Euler(50, -30, 0);
        light.intensity = 0.8f;

        GameObject gmObj = new GameObject("GameController");
        gmObj.AddComponent<GameManager>();

        GameObject dummyCube = GameObject.CreatePrimitive(PrimitiveType.Cube);
        dummyCube.name = "AntiShaderStrippingCube";
        dummyCube.transform.position = new Vector3(0, -5000, 0);

        string sceneDir = "Assets/Scenes";
        if (!Directory.Exists(sceneDir)) Directory.CreateDirectory(sceneDir);
        string scenePath = sceneDir + "/MainScene.unity";
        EditorSceneManager.SaveScene(newScene, scenePath);

        // ==========================================
        // 🚨 A MÁGICA GRÁFICA DO STUDIO-AI (URP) 🚨
        // ==========================================
        Debug.Log("[Studio-AI] A injetar o URP e Post-Processing...");
        AutoSetupURP.SetupURP(); // <--- Chama o nosso script de Néon antes de exportar!
        // ==========================================

        BuildPlayerOptions buildPlayerOptions = new BuildPlayerOptions();
        buildPlayerOptions.scenes = new[] { scenePath };
        buildPlayerOptions.locationPathName = "Builds/Game001.exe";
        buildPlayerOptions.target = BuildTarget.StandaloneWindows64;
        buildPlayerOptions.options = BuildOptions.None;

        BuildReport report = BuildPipeline.BuildPlayer(buildPlayerOptions);
        BuildSummary summary = report.summary;

        if (summary.result == BuildResult.Succeeded) {
            Debug.Log("Build succeeded: " + summary.totalSize + " bytes");
            EditorApplication.Exit(0);
        } else if (summary.result == BuildResult.Failed) {
            Debug.Log("Build failed");
            EditorApplication.Exit(1);
        }
    }
}