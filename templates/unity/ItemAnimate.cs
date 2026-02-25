using UnityEngine;

public class ItemAnimate : MonoBehaviour
{
    private float startY;

    void Start()
    {
        startY = transform.position.y;
    }

    void Update()
    {
        // Rotação constante para feedback visual de "item coletável"
        transform.Rotate(Vector3.up * 150f * Time.deltaTime, Space.World);

        // Movimento de levitação suave (Seno)
        float newY = startY + Mathf.Sin(Time.time * 3f) * 0.15f;
        transform.position = new Vector3(transform.position.x, newY, transform.position.z);
    }
}