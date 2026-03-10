import React, { useState, useEffect } from 'react';

export default function MarketingHub() {
  const [plan, setPlan] = useState([]);
  const [loading, setLoading] = useState(true);

  // Vai buscar o JSON gerado pela tua IA ao FastAPI
  useEffect(() => {
    fetch('http://localhost:8000/marketing/plan')
      .then(res => res.json())
      .then(data => {
        setPlan(data.plan || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Erro a contactar a API de Marketing:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="text-blue-400 text-xl animate-pulse font-semibold">A sintonizar com a rede social... 📡</div>;
  }

  return (
    <div className="animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-4xl font-bold text-blue-500 tracking-wide">🚀 HUB DE MARKETING</h2>
        <button className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-medium transition shadow-[0_0_10px_rgba(37,99,235,0.4)]">
          🤖 Gerar Novo Plano Semanal
        </button>
      </div>

      {plan.length === 0 ? (
        <div className="bg-gray-800 border border-gray-700 p-8 rounded-xl text-center">
          <p className="text-gray-400 mb-4">Ainda não tens nenhum plano de marketing gerado.</p>
          <p className="text-sm text-gray-500">Clica no botão acima para a IA analisar os níveis e escrever posts!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {plan.map((post, index) => (
            <div key={index} className="bg-gray-800 border border-gray-700 rounded-2xl p-6 shadow-lg hover:border-blue-500/50 transition-colors flex flex-col">

              {/* CABEÇALHO DA CARTA (Dia e Tipo) */}
              <div className="flex justify-between items-center mb-4 border-b border-gray-700 pb-3">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  📅 {post.dia}
                </h3>

                {/* Etiqueta colorida dependendo do tipo de post */}
                <span className={`text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider flex items-center gap-1 ${
                  post.tipo === 'Vídeo' ? 'bg-red-900/50 text-red-400 border border-red-700' :
                  post.tipo === 'Imagem' ? 'bg-purple-900/50 text-purple-400 border border-purple-700' :
                  'bg-blue-900/50 text-blue-400 border border-blue-700'
                }`}>
                  {post.tipo === 'Vídeo' ? '🎥' : post.tipo === 'Imagem' ? '🖼️' : '📝'} {post.tipo}
                </span>
              </div>

              {/* CORPO DO TEXTO (whitespace-pre-wrap mantém as quebras de linha da IA!) */}
              <div className="text-gray-300 text-sm whitespace-pre-wrap flex-1 mb-6 font-sans bg-gray-900/50 p-4 rounded-lg border border-gray-700/50">
                {post.texto}
              </div>

              {/* RODAPÉ (Aprovação) */}
              <div className="mt-auto pt-4 border-t border-gray-700 flex justify-between items-center">
                <span className="text-xs font-mono text-gray-500">
                  Status: {post.reviewed ? '✅ Aprovado' : '⏳ Aguarda Revisão'}
                </span>
                <button className="bg-gray-700 hover:bg-gray-600 text-white text-sm px-4 py-2 rounded transition">
                  Rever e Publicar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}