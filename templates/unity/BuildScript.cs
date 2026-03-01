using UnityEditor;
using UnityEngine;
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
                if (tagsProp.GetArrayElementAtIndex(i).stringValue == tagName)
                {
                    found = true;
                    break;
                }
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
        // 1. Criar uma nova cena limpa
        Scene newScene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        // 2. Configurar a Câmara Principal
        GameObject camObj = new GameObject("Main Camera");
        camObj.tag = "MainCamera";
        Camera cam = camObj.AddComponent<Camera>();
        cam.transform.position = new Vector3(0, 15, -10);
        cam.transform.rotation = Quaternion.Euler(60, 0, 0);

        // 3. Configurar uma Luz Global (Directional Light)
        GameObject lightObj = new GameObject("Directional Light");
        Light light = lightObj.AddComponent<Light>();
        light.type = LightType.Directional;
        light.transform.rotation = Quaternion.Euler(50, -30, 0);
        light.intensity = 0.8f; // Luz suave para a lanterna do jogador sobressair

        // 4. Instanciar o nosso novo e limpo GameManager
        GameObject gmObj = new GameObject("GameController");
        GameManager gm = gmObj.AddComponent<GameManager>();

        // (Removemos as atribuições antigas de obstacles, buildBorderWalls, etc.,
        // porque agora o LoadGenomeConfig() trata de tudo no Awake do GameManager)

        // 5. Guardar a cena no projeto
        string sceneDir = "Assets/Scenes";
        if (!Directory.Exists(sceneDir))
        {
            Directory.CreateDirectory(sceneDir);
        }
        string scenePath = sceneDir + "/MainScene.unity";
        EditorSceneManager.SaveScene(newScene, scenePath);

        // 6. Configurar as opções de Build do Executável (.exe)
        BuildPlayerOptions buildPlayerOptions = new BuildPlayerOptions();
        buildPlayerOptions.scenes = new[] { scenePath };
        buildPlayerOptions.locationPathName = "Builds/Game001.exe"; // Onde o Runner vai procurar!
        buildPlayerOptions.target = BuildTarget.StandaloneWindows64;
        buildPlayerOptions.options = BuildOptions.None;

        // 7. Mandar compilar!
        BuildPipeline.BuildPlayer(buildPlayerOptions);
    }
}