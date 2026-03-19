import React, { useState, useEffect } from 'react';

// 🚨 1. RECEBE A PROP 'showToast' DO APP.JSX
export default function ArtStudio({ showToast }) {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(null);
  const [theme, setTheme] = useState("Cyberpunk Neon");

  const fetchAssets = () => {
    fetch('http://localhost:8000/art/list')
      .then(res => res.json())
      .then(data => {
        setAssets(data.assets || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Erro ao carregar arte:", err);
        // 🚨 2. USA A FUNÇÃO GLOBAL SE O SERVIDOR ESTIVER EM BAIXO
        if (showToast) showToast("Erro ao ligar ao servidor de arte.", "error");
      });
  };

  useEffect(() => {
    fetchAssets();
  }, []);

  const handleGenerate = async (assetKey) => {
    setGenerating(assetKey);
    try {
      const response = await fetch('http://localhost:8000/art/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme: theme, asset_key: assetKey })
      });

      // 🚨 3. OBRIGA O JAVASCRIPT A LER ERROS DO BACK-END (Como o Erro 500)
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || "Erro interno do Servidor SD.");
      }

      // 🚨 4. SUCESSO! CHAMA O BALÃO VERDE GLOBAL
      if (showToast) showToast(`Arte gerada com sucesso! (${assetKey === "all" ? "Tudo" : assetKey})`, "success");
      fetchAssets();
    } catch (err) {
      console.error("Erro a gerar arte:", err);
      // 🚨 5. ERRO! CHAMA O BALÃO VERMELHO GLOBAL
      if (showToast) showToast(err.message, "error");
    }
    setGenerating(null);
  };

  if (loading) return <div className="text-purple-400 text-xl font-bold animate-pulse">A ligar ao Stable Diffusion... 🎨</div>;

  return (
    <div className="animate-fade-in relative">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-4xl font-bold text-purple-400 tracking-wide">🎨 ESTÚDIO DE ARTE</h2>

        <div className="flex gap-4 items-center">
            <div className="flex items-center gap-3 bg-gray-800 p-2 rounded-xl border border-gray-700">
              <span className="text-gray-400 font-medium pl-2">Tema:</span>
              <input
                type="text"
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                className="bg-gray-900 text-white px-4 py-2 rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none w-64"
                placeholder="Ex: Cyberpunk Neon, Medieval..."
              />
            </div>

            <button
              onClick={() => handleGenerate("all")}
              disabled={generating !== null}
              className={`px-6 py-3 rounded-xl font-bold transition flex items-center gap-2 ${
                generating !== null
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-purple-600 hover:bg-purple-500 text-white shadow-[0_0_10px_rgba(147,51,234,0.4)]'
              }`}
            >
              {generating === "all" ? '⏳ A pintar IA...' : '🖌️ Gerar Tudo'}
            </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {assets.map((asset) => {
          const folderType = asset.is_sprite ? "sprite" : "texture";
          const imageUrl = `http://localhost:8000/art/image/${folderType}/${asset.filename}`;
          const isGeneratingThis = generating === asset.id || generating === "all";

          return (
            <div key={asset.id} className="bg-gray-800 border border-gray-700 rounded-2xl p-4 flex flex-col items-center shadow-lg hover:border-purple-500/50 transition-colors">

              <h3 className="text-lg font-bold text-white mb-1 truncate w-full text-center" title={asset.name}>
                {asset.name}
              </h3>
              <span className="text-xs text-gray-400 mb-4">{asset.is_sprite ? '👾 Sprite (Sem Fundo)' : '🧱 Textura (Seamless)'}</span>

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
                {isGeneratingThis ? 'A Pintar...' : asset.status === "Pronto" ? '🔄 Recriar Imagem' : '🖌️ Gerar Arte'}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}