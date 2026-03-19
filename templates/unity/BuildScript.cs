using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements; // 🚨 Adicionado para PanelSettings
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;
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

        // 🚨 O TRUQUE MAGNÍFICO: Criar o PanelSettings do UI Toolkit via Código!
        string uiDir = "Assets/Resources/UI";
        if (!Directory.Exists(uiDir)) Directory.CreateDirectory(uiDir);
        string panelPath = uiDir + "/DefaultPanelSettings.asset";

        if (AssetDatabase.LoadAssetAtPath<PanelSettings>(panelPath) == null) {
            PanelSettings ps = ScriptableObject.CreateInstance<PanelSettings>();
            AssetDatabase.CreateAsset(ps, panelPath);
            AssetDatabase.SaveAssets();
            Debug.Log("[Studio-AI] DefaultPanelSettings gerado com sucesso!");
        }

        Scene newScene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

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

        BuildPlayerOptions buildPlayerOptions = new BuildPlayerOptions();
        buildPlayerOptions.scenes = new[] { scenePath };
        buildPlayerOptions.locationPathName = "Builds/Game001.exe";
        buildPlayerOptions.target = BuildTarget.StandaloneWindows64;
        buildPlayerOptions.options = BuildOptions.None;

        BuildPipeline.BuildPlayer(buildPlayerOptions);
    }
}