import React, { useState, useEffect } from 'react';

export default function ArtStudio() {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(null); // Guarda o ID ou "all"

  const fetchAssets = () => {
    fetch('http://localhost:8000/art/list')
      .then(res => res.json())
      .then(data => {
        setAssets(data.assets || []);
        setLoading(false);
      })
      .catch(err => console.error("Erro ao carregar arte:", err));
  };

  useEffect(() => {
    fetchAssets();
  }, []);

  const handleGenerate = async (assetKey) => {
    setGenerating(assetKey);
    try {
      // Pedido pode demorar bastante se for o "all"!
      await fetch('http://localhost:8000/art/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme: "Cyberpunk Neon", asset_key: assetKey })
      });
      fetchAssets(); // Atualiza as imagens após gerar
    } catch (err) {
      console.error("Erro a gerar arte:", err);
    }
    setGenerating(null);
  };

  if (loading) return <div className="text-purple-400 text-xl font-bold animate-pulse">A ligar ao Stable Diffusion... 🎨</div>;

  return (
    <div className="animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-4xl font-bold text-purple-400 tracking-wide">🎨 ESTÚDIO DE ARTE</h2>

        {/* BOTÃO MÁGICO PARA GERAR TUDO */}
        <button
          onClick={() => handleGenerate("all")}
          disabled={generating !== null}
          className={`px-6 py-2 rounded-lg font-medium transition flex items-center gap-2 ${
            generating !== null
              ? 'bg-gray-600 cursor-not-allowed'
              : 'bg-purple-600 hover:bg-purple-500 text-white shadow-[0_0_10px_rgba(147,51,234,0.4)]'
          }`}
        >
          {generating === "all" ? '⏳ A pintar IA (Pode demorar)...' : '🖌️ Gerar Todas as Artes'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {assets.map((asset) => {
          const folderType = asset.is_sprite ? "sprite" : "texture";
          const imageUrl = `http://localhost:8000/art/image/${folderType}/${asset.filename}`;
          // Se estiver a gerar o próprio ID ou se estiver a gerar "all", mostra o loading
          const isGeneratingThis = generating === asset.id || generating === "all";

          return (
            <div key={asset.id} className="bg-gray-800 border border-gray-700 rounded-2xl p-4 flex flex-col items-center shadow-lg hover:border-purple-500/50 transition-colors">

              <h3 className="text-lg font-bold text-white mb-1 truncate w-full text-center" title={asset.name}>
                {asset.name}
              </h3>
              <span className="text-xs text-gray-400 mb-4">{asset.is_sprite ? '👾 Sprite (Sem Fundo)' : '🧱 Textura (Seamless)'}</span>

              {/* MOLDURA DA IMAGEM */}
              <div className="w-48 h-48 bg-gray-900 border-2 border-dashed border-gray-600 rounded-xl mb-6 flex items-center justify-center overflow-hidden relative shadow-inner">
                {isGeneratingThis ? (
                  <div className="text-purple-500 animate-spin text-4xl">⏳</div>
                ) : asset.status === "Pronto" ? (
                  <img
                    src={`${imageUrl}?t=${new Date().getTime()}`}
                    alt={asset.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-gray-600 text-4xl opacity-50">🖼️</div>
                )}
              </div>

              {/* BOTÕES INDIVIDUAIS */}
              <button
                onClick={() => handleGenerate(asset.id)}
                disabled={generating !== null}
                className={`w-full py-3 rounded-lg font-bold transition-all transform ${
                  isGeneratingThis
                    ? 'bg-purple-900 text-purple-300 border border-purple-700 cursor-wait'
                    : generating !== null
                      ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                      : 'bg-purple-600 hover:bg-purple-500 text-white shadow-[0_0_10px_rgba(147,51,234,0.4)] hover:scale-105 active:scale-95'
                }`}
              >
                {isGeneratingThis ? 'A Pintar IA...' : asset.status === "Pronto" ? '🔄 Recriar Imagem' : '🖌️ Gerar Arte'}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}