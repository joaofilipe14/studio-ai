using UnityEngine;

public static class VoxelRenderer
{
    // Lógica isolada para processar a textura e criar o modelo 3D
    public static void CreateVoxelSprite(Transform parent, Texture2D rawTex, Material baseMaterial)
    {
        if (rawTex == null) return;

        // 1. Contornar a proteção de leitura (Read/Write) do Unity
        RenderTexture rt = RenderTexture.GetTemporary(rawTex.width, rawTex.height, 0, RenderTextureFormat.Default, RenderTextureReadWrite.Linear);
        Graphics.Blit(rawTex, rt);
        RenderTexture previous = RenderTexture.active;
        RenderTexture.active = rt;

        Texture2D readableTex = new Texture2D(rawTex.width, rawTex.height);
        readableTex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
        readableTex.Apply();

        RenderTexture.active = previous;
        RenderTexture.ReleaseTemporary(rt);

        readableTex.filterMode = FilterMode.Point;

        // 2. Construir os Voxels
        int step = Mathf.Max(1, readableTex.width / 32);
        float voxelSize = (float)step / readableTex.width;
        int cubeCount = 0;

        MaterialPropertyBlock propBlock = new MaterialPropertyBlock();

        for (int y = 0; y < readableTex.height; y += step) {
            for (int x = 0; x < readableTex.width; x += step) {
                Color color = readableTex.GetPixel(x, y);

                if (color.a > 0.1f) {
                    GameObject voxel = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    voxel.transform.SetParent(parent);

                    voxel.transform.localPosition = new Vector3(
                        (x - readableTex.width / 2f) / readableTex.width,
                        (float)y / readableTex.width,
                        0
                    );

                    voxel.transform.localScale = Vector3.one * voxelSize;

                    Renderer rend = voxel.GetComponent<Renderer>();
                    rend.sharedMaterial = baseMaterial;

                    propBlock.SetColor("_Color", color);
                    propBlock.SetColor("_BaseColor", color);
                    rend.SetPropertyBlock(propBlock);

                    Object.Destroy(voxel.GetComponent<BoxCollider>());
                    cubeCount++;
                }
            }
        }

        if (cubeCount == 0) {
            GameObject fallback = GameObject.CreatePrimitive(PrimitiveType.Cube);
            fallback.transform.SetParent(parent);
            fallback.GetComponent<Renderer>().material = baseMaterial;
        } else {
            Debug.Log($"🎨 [VoxelRenderer] Gerou modelo com {cubeCount} blocos.");
        }
    }
}