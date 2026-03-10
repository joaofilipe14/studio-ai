import React, { useState, useEffect, useRef } from 'react';

export default function AudioStudio() {
  const [activeTab, setActiveTab] = useState('bgm');
  const [tracks, setTracks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  // Elemento de áudio invisível para tocar os sons
  const audioPlayer = useRef(new Audio());

  const fetchAudioList = () => {
    fetch('http://localhost:8000/audio/list')
      .then(res => res.json())
      .then(data => {
        setTracks(data.tracks || []);
        setLoading(false);
      })
      .catch(err => console.error("Erro ao carregar áudios:", err));
  };

  useEffect(() => {
    fetchAudioList();
  }, []);

  const playSound = (filename) => {
    audioPlayer.current.src = `http://localhost:8000/audio/play/${filename}`;
    audioPlayer.current.play();
  };

  const handleGenerate = async (assetKey) => {
    setGenerating(true);
    try {
      // Como o MusicGen da Meta é pesado, isto pode demorar um bocado!
      await fetch('http://localhost:8000/audio/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme_name: "Cyberpunk Neon", asset_key: assetKey })
      });
      fetchAudioList(); // Recarrega a lista para mostrar "Pronto"
    } catch (err) {
      console.error("Erro a gerar áudio:", err);
    }
    setGenerating(false);
  };

  if (loading) return <div className="text-green-400 text-xl font-bold animate-pulse">A ligar à Mesa de Mistura... 🎛️</div>;

  const currentList = tracks.filter(t => activeTab === 'bgm' ? t.type === 'BGM' : t.type === 'SFX');

  return (
    <div className="animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-4xl font-bold text-green-400 tracking-wide">🎵 LABORATÓRIO DE ÁUDIO</h2>
        <button
          onClick={() => handleGenerate("all")}
          disabled={generating}
          className={`px-6 py-2 rounded-lg font-medium transition flex items-center gap-2 ${
            generating ? 'bg-gray-600 cursor-not-allowed' : 'bg-green-600 hover:bg-green-500 text-white shadow-[0_0_10px_rgba(34,197,94,0.4)]'
          }`}
        >
          {generating ? '⏳ A processar IA (Pode demorar)...' : '🎙️ Gerar Todos os Sons'}
        </button>
      </div>

      <div className="flex space-x-4 mb-6 border-b border-gray-700 pb-4">
        <button onClick={() => setActiveTab('bgm')} className={`px-6 py-2 rounded-lg font-bold transition-all ${activeTab === 'bgm' ? 'bg-green-900/50 text-green-400 border border-green-700' : 'text-gray-400 hover:bg-gray-800'}`}>🎹 Músicas de Fundo</button>
        <button onClick={() => setActiveTab('sfx')} className={`px-6 py-2 rounded-lg font-bold transition-all ${activeTab === 'sfx' ? 'bg-green-900/50 text-green-400 border border-green-700' : 'text-gray-400 hover:bg-gray-800'}`}>🔊 Efeitos Sonoros</button>
      </div>

      <div className="space-y-4">
        {currentList.map((track) => (
          <div key={track.id} className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex items-center justify-between shadow-md">

            <div className="flex items-center gap-4">
              <button
                onClick={() => playSound(track.filename)}
                disabled={track.status !== "Pronto"}
                className={`w-12 h-12 rounded-full flex items-center justify-center text-xl transition-all ${
                  track.status !== "Pronto" ? 'bg-gray-700 text-gray-500 opacity-50' : 'bg-green-600 hover:bg-green-500 text-white shadow-[0_0_10px_rgba(34,197,94,0.4)] hover:scale-105'
                }`}
              >
                ▶️
              </button>

              <div>
                <h3 className="text-xl font-bold text-white flex items-center gap-2">{track.name}</h3>
                <span className={`px-2 py-0.5 rounded text-xs font-bold ${track.status !== "Pronto" ? 'bg-yellow-900/50 text-yellow-500' : 'bg-green-900/50 text-green-500'}`}>
                  {track.status}
                </span>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => handleGenerate(track.name)}
                disabled={generating}
                className="px-4 py-2 bg-purple-700 hover:bg-purple-600 disabled:opacity-50 text-white rounded transition text-sm font-bold"
              >
                {generating ? '⏳' : '🤖 Recriar IA'}
              </button>
            </div>

          </div>
        ))}
      </div>
    </div>
  );
}