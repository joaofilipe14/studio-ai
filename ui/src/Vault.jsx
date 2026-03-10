import React, { useState, useEffect } from 'react';

export default function Vault() {
  const [playerData, setPlayerData] = useState(null);
  const [roster, setRoster] = useState([]);
  const [loading, setLoading] = useState(true);

  // Assim que a página abre, vai buscar os dados ao Python!
  useEffect(() => {
    Promise.all([
      fetch('http://localhost:8000/player/data').then(res => res.json()),
      fetch('http://localhost:8000/player/roster').then(res => res.json())
    ])
    .then(([playerRes, rosterRes]) => {
      setPlayerData(playerRes);
      setRoster(rosterRes.classes || []);
      setLoading(false);
    })
    .catch(err => {
      console.error("Erro a contactar a API:", err);
      setLoading(false);
    });
  }, []);

  // Ecrã de carregamento super rápido
  if (loading) {
    return <div className="text-cyan-400 text-xl animate-pulse font-semibold">A decifrar a porta do Cofre... ⏳</div>;
  }

  // Se o servidor Python estiver desligado
  if (!playerData) {
    return <div className="text-red-500 bg-red-900/20 p-4 rounded-lg border border-red-800">
      🚨 Erro: Não foi possível ligar ao Servidor Central (FastAPI). Verifica se está a correr!
    </div>;
  }

  return (
    <div className="animate-fade-in">
      <h2 className="text-4xl font-bold text-yellow-500 mb-2 tracking-wide">🏦 O COFRE</h2>
      <div className="flex items-center space-x-6 mb-10 bg-gray-800 p-4 rounded-xl border border-gray-700 inline-flex shadow-md">
        <p className="text-xl">
          <span className="text-gray-400">Saldo: </span>
          <span className="font-bold text-yellow-400">{playerData.wallet.totalCoins} Moedas</span>
        </p>
        <div className="w-px h-6 bg-gray-600"></div>
        <p className="text-xl">
          <span className="text-gray-400">Vidas: </span>
          <span className="font-bold text-red-400">{playerData.stats.currentLives} / {playerData.stats.maxLives}</span>
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* ---------------- CARTA: VIDA EXTRA ---------------- */}
        <div className="bg-gray-800 border border-gray-700 rounded-2xl p-6 flex flex-col items-center shadow-lg hover:border-red-500/50 transition-colors">
          <div className="text-7xl mb-4 drop-shadow-[0_0_15px_rgba(239,68,68,0.6)]">❤️</div>
          <h3 className="text-2xl font-bold text-white mb-2">Vida Extra</h3>
          <p className="text-gray-400 text-center mb-6 text-sm">Sente-te mais seguro com uma vida de reserva para a campanha.</p>
          <button className="mt-auto w-full bg-green-600 hover:bg-green-500 text-white font-bold py-3 rounded-lg transition-all transform hover:scale-105 active:scale-95 shadow-[0_0_10px_rgba(22,163,74,0.4)]">
            Comprar (50 M)
          </button>
        </div>

        {/* ---------------- CARTAS DO ROSTER ---------------- */}
        {roster.map((char) => {
          const isUnlocked = playerData.unlockedClasses.includes(char.id);
          const isEquipped = playerData.loadout.selectedClassID === char.id;

          return (
            <div key={char.id} className={`border rounded-2xl p-6 flex flex-col items-center shadow-lg transition-colors ${
              isEquipped ? 'bg-cyan-900/20 border-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.2)]' : 'bg-gray-800 border-gray-700 hover:border-gray-500'
            }`}>
              <div className="text-7xl mb-4 opacity-90 drop-shadow-[0_0_10px_rgba(255,255,255,0.2)]">👾</div>
              <h3 className="text-2xl font-bold text-white mb-1">{char.name}</h3>
              <p className="text-gray-400 text-xs text-center mb-4 min-h-[32px]">{char.description}</p>

              <div className="w-full bg-gray-900/80 rounded-lg p-3 mb-6 text-sm border border-gray-700">
                <div className="flex justify-between mb-1"><span className="text-gray-500">Velocidade:</span> <span className="text-yellow-400 font-mono">{char.stats.speed}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Visão:</span> <span className="text-cyan-400 font-mono">{char.stats.visionRadius}m</span></div>
              </div>

              {isEquipped ? (
                <button className="mt-auto w-full bg-cyan-800/50 text-cyan-300 font-bold py-3 rounded-lg cursor-default border border-cyan-700">
                  ✔️ Equipado
                </button>
              ) : isUnlocked ? (
                <button className="mt-auto w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg transition-all transform hover:scale-105 active:scale-95 shadow-[0_0_10px_rgba(37,99,235,0.4)]">
                  Equipar
                </button>
              ) : (
                <button className="mt-auto w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-3 rounded-lg transition-all transform hover:scale-105 active:scale-95 shadow-[0_0_10px_rgba(147,51,234,0.4)]">
                  Comprar ({char.cost} M)
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}