using UnityEngine;
using System.Collections;
using System.IO;

public class TrailerDirector : MonoBehaviour {
    [Header("Configurações Cinemáticas")]
    public float radius = 7f;           // 🚨 (Antes era 15) Mais perto do herói!
    public float height = 5f;           // 🚨 (Antes era 12) Desce o drone para ficar mais raso!
    public float orbitSpeed = 40f;      // 🚨 (Antes era 30) Um bocadinho mais rápido para dar dinamismo
    public int frameRate = 30;
    public int durationSeconds = 4;     // Quantos segundos dura o vídeo

    private bool isRecording = false;
    private float currentAngle = 0f;
    private string saveFolder;
    private Transform targetCenter;

    // Guarda a câmara original para devolver o controlo no fim
    private Camera originalCamera;
    private Camera cinematicCamera;

    void Awake() {
        // Define a pasta onde os frames vão ser guardados (dentro do workspace!)
        saveFolder = Path.Combine(Application.dataPath, "..", "..", "workspace", "marketing", "trailer_frames");

        // Cria a câmara cinemática
        GameObject camObj = new GameObject("CinematicCamera");
        cinematicCamera = camObj.AddComponent<Camera>();
        cinematicCamera.enabled = false; // Começa desligada
    }

    public void StartHeroShot(Vector3 mapCenter, string folderPath, System.Action onCompleteCallback = null)
    {
        if (isRecording) return;

        saveFolder = folderPath;
        if (string.IsNullOrEmpty(saveFolder)) {
            saveFolder = Path.Combine(Application.dataPath, "..", "trailer_test");
        }

        Debug.Log($"[TRAILER DIRECTOR] A iniciar gravação orbital em: {saveFolder}");

        if (Directory.Exists(saveFolder)) {
            DirectoryInfo di = new DirectoryInfo(saveFolder);
            foreach (FileInfo file in di.GetFiles()) file.Delete();
        } else {
            Directory.CreateDirectory(saveFolder); // <-- Já não dá null!
        }
        if (cinematicCamera == null) {
            GameObject camObj = new GameObject("CinematicCamera");
            cinematicCamera = camObj.AddComponent<Camera>();

            // Fundo preto puro para destacar o Neon
            cinematicCamera.clearFlags = CameraClearFlags.SolidColor;
            cinematicCamera.backgroundColor = Color.black;

            // 💡 NOVO: Adiciona um "Searchlight" (Holofote) colado à câmara!
            Light droneLight = camObj.AddComponent<Light>();
            droneLight.type = LightType.Spot;
            droneLight.spotAngle = 100f; // Cone largo para iluminar bastante
            droneLight.range = 25f;      // Alcance da luz
            droneLight.intensity = 5f;   // Intensidade forte (ajusta se ficar muito claro)
            droneLight.color = new Color(0.8f, 0.9f, 1f);
        }

        if (targetCenter == null) targetCenter = new GameObject("MapCenterPoint").transform;
        targetCenter.position = mapCenter;

        originalCamera = Camera.main;
        if (originalCamera != null) originalCamera.enabled = false;
        cinematicCamera.enabled = true;

        Time.captureFramerate = frameRate;
        isRecording = true;

        StartCoroutine(RecordOrbitSequence(onCompleteCallback));
    }

    // 2. Recebemos o callback aqui
    IEnumerator RecordOrbitSequence(System.Action onCompleteCallback)
    {
        int totalFrames = frameRate * durationSeconds;

        for (int frame = 0; frame < totalFrames; frame++)
        {
            currentAngle += orbitSpeed * Time.deltaTime;
            float rad = currentAngle * Mathf.Deg2Rad;
            Vector3 newPos = targetCenter.position + new Vector3(Mathf.Cos(rad) * radius, height, Mathf.Sin(rad) * radius);
            cinematicCamera.transform.position = newPos;
            cinematicCamera.transform.LookAt(targetCenter);

            string filename = string.Format("{0}/frame_{1:D4}.png", saveFolder, frame);
            ScreenCapture.CaptureScreenshot(filename);
            yield return new WaitForEndOfFrame();
        }

        isRecording = false;
        Time.captureFramerate = 0;
        if (cinematicCamera != null) cinematicCamera.enabled = false;
        if (originalCamera != null) originalCamera.enabled = true;

        Debug.Log($"[TRAILER DIRECTOR] Gravação concluída! {totalFrames} frames salvos.");

        // 3. Executa a ação de fechar o jogo!
        if (onCompleteCallback != null) onCompleteCallback.Invoke();
    }
}