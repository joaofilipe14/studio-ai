import React, { useState, useEffect } from 'react';

export default function Vault() {
  const [playerData, setPlayerData] = useState(null);
  const [rosterClasses, setRosterClasses] = useState([]);
  const [rosterItems, setRosterItems] = useState([]);
  const [loading, setLoading] = useState(true);

  // Assim que a página abre, vai buscar os dados ao Python!
  useEffect(() => {
    Promise.all([
      fetch('http://localhost:8000/player/data').then(res => res.json()),
      fetch('http://localhost:8000/player/roster').then(res => res.json())
    ])
    .then(([playerRes, rosterRes]) => {
      setPlayerData(playerRes);
      setRosterClasses(rosterRes.classes || []);
      setRosterItems(rosterRes.items || []);
      setLoading(false);
    })
    .catch(err => {
      console.error("Erro a contactar a API:", err);
      setLoading(false);
    });
  }, []);

  // Emojis de Fallback (caso a IA ainda não tenha gerado a imagem)
  const getItemFallbackIcon = (id) => {
    if (id.includes('life')) return '❤️';
    if (id.includes('time')) return '⏳';
    if (id.includes('speed')) return '⚡';
    if (id.includes('trap')) return '🛡️';
    if (id.includes('luck')) return '🍀';
    return '🔮';
  };

  if (loading) {
    return <div className="text-cyan-400 text-xl animate-pulse font-semibold">A decifrar a porta do Cofre... ⏳</div>;
  }

  if (!playerData) {
    return <div className="text-red-500 bg-red-900/20 p-4 rounded-lg border border-red-800">
      🚨 Erro: Não foi possível ligar ao Servidor Central (FastAPI). Verifica se está a correr!
    </div>;
  }

  return (
    <div className="animate-fade-in pb-10">
      <h2 className="text-4xl font-bold text-yellow-500 mb-2 tracking-wide">🏦 O COFRE (META-PROGRESSO)</h2>

      <div className="flex items-center space-x-6 mb-8 bg-gray-800 p-4 rounded-xl border border-gray-700 inline-flex shadow-md">
        <p className="text-xl">
          <span className="text-gray-400">Moedas (Run): </span>
          <span className="font-bold text-yellow-400">{playerData.wallet.totalCoins} 🪙</span>
        </p>
        <div className="w-px h-6 bg-gray-600"></div>
        <p className="text-xl">
          <span className="text-gray-400">Cristais (Cofre): </span>
          <span className="font-bold text-cyan-400">{playerData.wallet.timeCrystals} 💠</span>
        </p>
        <div className="w-px h-6 bg-gray-600"></div>
        <p className="text-xl">
          <span className="text-gray-400">Vidas Iniciais: </span>
          <span className="font-bold text-red-400">{playerData.stats.maxLives} ❤️</span>
        </p>
      </div>

      {/* ================= SECÇÃO 1: HERÓIS ================= */}
      <h3 className="text-2xl font-bold text-cyan-400 mb-4 border-b border-cyan-900 pb-2">Desbloquear Heróis</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        {rosterClasses.map((char) => {
          const isUnlocked = playerData.unlockedClasses.includes(char.id) || char.cost === 0;
          const isEquipped = playerData.loadout.selectedClassID === char.id;

          // 🚨 A TUA NOVA LÓGICA DE ROTAS E CACHE (Como as personagens são sprites, vai buscar à pasta sprite)
          const imgUrl = `http://localhost:8000/art/image/sprite/${char.spriteName}.png`;

          return (
            <div key={char.id} className={`border rounded-2xl p-6 flex flex-col items-center shadow-lg transition-all duration-300 ${
              isEquipped ? 'bg-cyan-900/20 border-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.2)] scale-105' : 'bg-gray-800 border-gray-700 hover:border-gray-500 hover:bg-gray-800/80'
            }`}>

              {/* IMAGEM DO HERÓI */}
              <div className="w-32 h-32 bg-gray-900 border-2 border-dashed border-gray-600 rounded-xl mb-4 flex items-center justify-center overflow-hidden relative shadow-inner">
                <img
                  src={`${imgUrl}?t=${new Date().getTime()}`}
                  alt={char.name}
                  className="w-full h-full object-cover pixelated"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'block';
                  }}
                />
                {/* Fallback caso a IA ainda não tenha gerado */}
                <div className="text-6xl hidden drop-shadow-[0_0_10px_rgba(255,255,255,0.2)]">👾</div>
              </div>

              <h3 className="text-2xl font-bold text-white mb-1">{char.name}</h3>
              <p className="text-gray-400 text-xs text-center mb-4 min-h-[32px]">{char.description}</p>

              <div className="w-full bg-gray-900/80 rounded-lg p-3 mb-6 text-sm border border-gray-700">
                <div className="flex justify-between mb-1"><span className="text-gray-500">Velocidade:</span> <span className="text-yellow-400 font-mono">{char.stats.speed}</span></div>
                <div className="flex justify-between mb-1"><span className="text-gray-500">Visão:</span> <span className="text-cyan-400 font-mono">{char.stats.visionRadius}m</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Vidas Base:</span> <span className="text-red-400 font-mono">{char.stats.baseLives}</span></div>
              </div>

              {isEquipped ? (
                <button className="mt-auto w-full bg-cyan-800/50 text-cyan-300 font-bold py-3 rounded-lg cursor-default border border-cyan-700">
                  ✔️ EQUIPADO
                </button>
              ) : isUnlocked ? (
                <button className="mt-auto w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg transition-all shadow-[0_0_10px_rgba(37,99,235,0.4)]">
                  EQUIPAR
                </button>
              ) : (
                <button className="mt-auto w-full bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-3 rounded-lg transition-all shadow-[0_0_10px_rgba(6,182,212,0.4)]">
                  COMPRAR ({char.cost} 💠)
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* ================= SECÇÃO 2: UPGRADES PERMANENTES ================= */}
      <h3 className="text-2xl font-bold text-purple-400 mb-4 border-b border-purple-900 pb-2">Upgrades do Cofre</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {rosterItems.map((item) => {
          // 🚨 A TUA NOVA LÓGICA DE ROTAS E CACHE (Para os items)
          const imgUrl = `http://localhost:8000/art/image/sprite/${item.id}.png`;

          return (
            <div key={item.id} className="bg-gray-800 border border-gray-700 rounded-2xl p-6 flex flex-col items-center shadow-lg hover:border-purple-500/50 hover:bg-gray-800/80 transition-all duration-300">

              {/* IMAGEM DO UPGRADE */}
              <div className="w-24 h-24 bg-gray-900 border-2 border-dashed border-purple-900/50 rounded-full mb-4 flex items-center justify-center overflow-hidden relative shadow-[0_0_15px_rgba(168,85,247,0.2)]">
                <img
                  src={`${imgUrl}?t=${new Date().getTime()}`}
                  alt={item.name}
                  className="w-full h-full object-cover pixelated"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'block';
                  }}
                />
                {/* Fallback Emoji */}
                <div className="text-5xl hidden drop-shadow-[0_0_10px_rgba(168,85,247,0.6)]">
                  {getItemFallbackIcon(item.id)}
                </div>
              </div>

              <h3 className="text-lg font-bold text-white mb-2 text-center h-14 flex items-center">{item.name}</h3>
              <p className="text-gray-400 text-center mb-6 text-xs flex-grow">{item.description}</p>

              <div className="w-full mb-4 text-center">
                <span className="text-xs text-purple-300 bg-purple-900/30 px-3 py-1 rounded-full border border-purple-800">
                  Nível Atual: {
                    item.id === 'item_life' ? (playerData.stats.maxLives - 3) :
                    item.id === 'item_time_boost' ? playerData.purchasedUpgrades.startExtraTimeLvl :
                    item.id === 'item_perm_speed' ? playerData.purchasedUpgrades.permSpeedLvl :
                    item.id === 'item_trap_reduction' ? playerData.purchasedUpgrades.trapReductionLvl :
                    (playerData.unlockedClasses.includes(item.id) ? 'Desbloqueado' : '0')
                  }
                </span>
              </div>

              <button className="mt-auto w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-3 rounded-lg transition-all shadow-[0_0_10px_rgba(147,51,234,0.4)]">
                COMPRAR ({item.cost} 💠)
              </button>
            </div>
          );
        })}
      </div>

    </div>
  );
}