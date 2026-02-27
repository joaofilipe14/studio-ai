using UnityEngine;

public class CameraController : MonoBehaviour
{
    public Transform target;
    public bool isHumanMode = false;

    [Header("Human Settings")]
    public float mouseSensitivity = 3f;
    public float distance = 5f;
    public float heightOffset = 1.5f;
    private float pitch = 20f;
    private float yaw = 0f;

    [Header("AI Settings")]
    public Vector3 aiOffset = new Vector3(0, 15, -10);
    public float aiSmoothSpeed = 5f;

    void Start()
    {
        if (isHumanMode)
        {
            Cursor.lockState = CursorLockMode.Locked; // Esconde e prende o rato no centro
            Cursor.visible = false;
            // Alinha o yaw inicial com a rotação do target
            if (target != null) yaw = target.eulerAngles.y;
        }
    }

    void LateUpdate()
    {
        if (target == null) return;

        if (isHumanMode)
        {
            // Rotação com o Rato
            yaw += Input.GetAxis("Mouse X") * mouseSensitivity;
            pitch -= Input.GetAxis("Mouse Y") * mouseSensitivity;
            pitch = Mathf.Clamp(pitch, -15f, 75f); // Impede de dar a volta completa

            // Posicionamento Orbital
            Quaternion rotation = Quaternion.Euler(pitch, yaw, 0);
            Vector3 direction = new Vector3(0, 0, -distance);
            Vector3 targetHead = target.position + Vector3.up * heightOffset;

            transform.position = targetHead + rotation * direction;
            transform.LookAt(targetHead);
        }
        else
        {
            // Câmara Isométrica/Top-Down para o Bot
            Vector3 desiredPosition = target.position + aiOffset;
            transform.position = Vector3.Lerp(transform.position, desiredPosition, Time.deltaTime * aiSmoothSpeed);
            transform.LookAt(target.position);
        }
    }
}