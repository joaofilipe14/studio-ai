using UnityEngine;

public class VoxelParticle : MonoBehaviour {
    void Start() {
        // Destrói a partícula após 2 a 4 segundos
        Destroy(gameObject, Random.Range(2f, 4f));
    }
}