#if UNITY_EDITOR
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public class AutoSetupURP : EditorWindow
{
    public static void SetupURP()
    {
        // 🚨 Corrigido: Uso do defaultRenderPipeline moderno
        if (GraphicsSettings.defaultRenderPipeline == null)
        {
            Debug.LogWarning("[Studio-AI] Aviso: Tens de criar e arrastar o URP Asset para os Project Settings > Graphics primeiro!");
        }

        UpgradeMaterials();
        SetupCamera();
        SetupGlobalVolume();

        Debug.Log("<b>[Studio-AI]</b> ✨ Magia Concluída! URP e Post-Processing configurados na cena.");
    }

    static void UpgradeMaterials()
    {
        string[] guids = AssetDatabase.FindAssets("t:Material");
        int upgraded = 0;
        Shader urpLit = Shader.Find("Universal Render Pipeline/Lit");
        Shader urpUnlit = Shader.Find("Universal Render Pipeline/Unlit");

        foreach (string guid in guids)
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            Material mat = AssetDatabase.LoadAssetAtPath<Material>(path);

            if (mat != null && mat.shader != null)
            {
                if (mat.shader.name == "Standard")
                {
                    mat.shader = urpLit;
                    upgraded++;
                }
                else if (mat.shader.name == "Unlit/Color" || mat.shader.name == "Unlit/Texture")
                {
                    mat.shader = urpUnlit;
                    upgraded++;
                }
            }
        }
        Debug.Log($"[Studio-AI] 🎨 {upgraded} Materiais atualizados para a nova geração (URP).");
        AssetDatabase.SaveAssets();
    }

    static void SetupCamera()
    {
        Camera mainCam = Camera.main;
        if (mainCam != null)
        {
            UniversalAdditionalCameraData camData = mainCam.GetComponent<UniversalAdditionalCameraData>();
            if (camData == null) camData = mainCam.gameObject.AddComponent<UniversalAdditionalCameraData>();

            camData.renderPostProcessing = true;
            Debug.Log("[Studio-AI] 🎥 Câmara principal ativada para ler Post-Processing.");
        }
    }

    static void SetupGlobalVolume()
    {
        // 🚨 Corrigido: Uso do FindFirstObjectByType moderno
        if (Object.FindFirstObjectByType<Volume>() != null)
        {
            Debug.Log("[Studio-AI] Já existe um Volume de efeitos na cena. A ignorar...");
            return;
        }

        GameObject volumeGO = new GameObject("Global Volume (Studio-AI)");
        Volume volume = volumeGO.AddComponent<Volume>();
        volume.isGlobal = true;

        VolumeProfile profile = ScriptableObject.CreateInstance<VolumeProfile>();

        // 🚨 Corrigido: Sem erro do 'out', guardamos a variável diretamente!
        Bloom bloom = profile.Add<Bloom>();
        if (bloom != null)
        {
            bloom.intensity.Override(3.5f);
            bloom.threshold.Override(0.8f);
            bloom.scatter.Override(0.7f);
        }

        ColorAdjustments colorAdj = profile.Add<ColorAdjustments>();
        if (colorAdj != null)
        {
            colorAdj.postExposure.Override(0.5f);
            colorAdj.saturation.Override(25f);
            colorAdj.contrast.Override(15f);
        }

        Vignette vignette = profile.Add<Vignette>();
        if (vignette != null)
        {
            vignette.intensity.Override(0.35f);
            vignette.color.Override(Color.black);
            vignette.smoothness.Override(0.4f);
        }

        if (!AssetDatabase.IsValidFolder("Assets/Settings"))
        {
            AssetDatabase.CreateFolder("Assets", "Settings");
        }

        string assetPath = "Assets/Settings/CyberpunkProfile.asset";
        AssetDatabase.CreateAsset(profile, assetPath);
        AssetDatabase.SaveAssets();

        volume.profile = profile;

        Debug.Log($"[Studio-AI] 🎆 Global Volume de Néon e Bloom criado e guardado em {assetPath}!");
    }
}
#endif