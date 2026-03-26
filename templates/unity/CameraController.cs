using UnityEngine;

public class CameraController : MonoBehaviour
{
    public Transform target;
    public bool isHumanMode = false;

    [Header("Human Settings")]
    public float mouseSensitivity = 3f;
    public float distance = 5f;
    public float heightOffset = 1.5f;
    public float rotationSmoothing = 10f;
    private float pitch = 20f;
    private float yaw = 0f;
    private float currentYaw = 0f;
    private float currentPitch = 20f;

    [Header("AI Settings")]
    public Vector3 aiOffset = new Vector3(0, 15, -10);
    public float aiSmoothTime = 0.3f;
    public float aiSmoothSpeed = 5f;
    private Vector3 currentVelocity = Vector3.zero;

    [Header("Juice - Shake")]
    private float shakeDuration = 0f;
    private float shakeMagnitude = 0.1f;
    private Vector3 shakeOffset = Vector3.zero;

    void Start() {
        if (isHumanMode) {
            if (target != null) {
                yaw = target.eulerAngles.y;
                currentYaw = yaw;
            }
        }
    }

    void LateUpdate() {
        if (target == null) return;
        if (isHumanMode) {
            // 1. Ler Input
            yaw += Input.GetAxis("Mouse X") * mouseSensitivity;
            pitch -= Input.GetAxis("Mouse Y") * mouseSensitivity;
            pitch = Mathf.Clamp(pitch, -15f, 75f);

            // 2. Suavizar a rotação (Interpolação)
            currentYaw = Mathf.LerpAngle(currentYaw, yaw, Time.deltaTime * rotationSmoothing);
            currentPitch = Mathf.Lerp(currentPitch, pitch, Time.deltaTime * rotationSmoothing);

            // 3. Calcular posição baseada na rotação suavizada
            Quaternion rotation = Quaternion.Euler(currentPitch, currentYaw, 0);
            Vector3 direction = new Vector3(0, 0, -distance);
            Vector3 targetHead = target.position + Vector3.up * heightOffset;

            transform.position = targetHead + rotation * direction;
            transform.LookAt(targetHead);
            if (shakeDuration > 0) {
                shakeOffset = Random.insideUnitSphere * shakeMagnitude;
                shakeDuration -= Time.deltaTime;
            } else {
                shakeOffset = Vector3.zero;
            }
            transform.position += shakeOffset;
        } else {
            // Câmara Isométrica Suave para o Bot (Amortecimento Gradual)
            Vector3 desiredPosition = target.position + aiOffset;
            transform.position = Vector3.SmoothDamp(transform.position, desiredPosition, ref currentVelocity, aiSmoothTime);

            // Suaviza o olhar para o target
            Quaternion targetRotation = Quaternion.LookRotation(target.position - transform.position);
            transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, Time.deltaTime * 5f);
        }
    }

    public void TriggerShake(float duration, float magnitude) {
        shakeDuration = duration;
        shakeMagnitude = magnitude;
    }
}