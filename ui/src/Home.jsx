import React, { useState, useEffect } from 'react';

export default function Home() {
  const [summary, setSummary] = useState({
    player: { name: '-', coins: 0, level: 1, wins: 0 },
    evolution: { total_generations: 0, latest_level: 1 },
    hall_of_fame: 0
  });
  const [loading, setLoading] = useState(true);

  const fetchSummary = () => {
    fetch('http://localhost:8000/dashboard/summary')
      .then(res => res.json())
      .then(data => {
        setSummary(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Erro ao carregar o resumo:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchSummary();
    const interval = setInterval(fetchSummary, 5000); // Atualiza a cada 5 segundos
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="text-yellow-500 text-xl font-bold animate-pulse">A ligar aos Servidores Centrais... 🌐</div>;

  return (
    <div className="animate-fade-in text-white space-y-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-4xl font-bold text-yellow-500 tracking-wide uppercase">Studio-AI Command Center</h2>
          <p className="text-gray-400 mt-2">Visão geral do ecossistema e saúde da campanha de desenvolvimento.</p>
        </div>
        <div className="flex items-center gap-3 bg-green-900/30 border border-green-500 text-green-400 px-4 py-2 rounded-lg shadow-[0_0_15px_rgba(34,197,94,0.2)]">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-ping"></div>
          <span className="font-bold text-sm uppercase tracking-wider">Sistema Online</span>
        </div>
      </div>

      {/* GRELHA DE MÉTRICAS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

        {/* CARD 1: Cérebro da IA */}
        <div className="bg-gray-800 p-6 rounded-2xl border border-blue-500/50 shadow-[0_0_20px_rgba(59,130,246,0.1)] hover:border-blue-500 transition-all duration-300 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-bl-full -mr-10 -mt-10 group-hover:bg-blue-500/20 transition-all"></div>
          <h3 className="text-gray-400 text-sm font-bold uppercase tracking-wider mb-2">🧠 Esforço da IA (Bot)</h3>
          <div className="flex items-end gap-4">
            <span className="text-5xl font-black text-white">{summary.evolution.total_generations}</span>
            <span className="text-blue-400 font-medium mb-1">Gerações Criadas</span>
          </div>
          <div className="mt-6 text-sm text-gray-400 bg-gray-900/50 p-3 rounded-lg">
            A trabalhar/encravado no momento no <span className="text-white font-bold">Nível {summary.evolution.latest_level}</span>.
          </div>
        </div>

        {/* CARD 2: Progresso do Jogador (Humano) */}
        <div className="bg-gray-800 p-6 rounded-2xl border border-green-500/50 shadow-[0_0_20px_rgba(34,197,94,0.1)] hover:border-green-500 transition-all duration-300 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-green-500/10 rounded-bl-full -mr-10 -mt-10 group-hover:bg-green-500/20 transition-all"></div>
          <h3 className="text-gray-400 text-sm font-bold uppercase tracking-wider mb-2">👤 {summary.player.name} (Humano)</h3>
          <div className="flex justify-between items-end">
            <div>
              <span className="text-5xl font-black text-white">Lvl {summary.player.level}</span>
              <p className="text-green-400 font-medium mt-1">Nível Alcançado</p>
            </div>
            <div className="text-right">
              <p className="text-xl font-bold text-yellow-400">💰 {summary.player.coins}</p>
              <p className="text-sm text-gray-500">Moedas globais</p>
            </div>
          </div>
        </div>

        {/* CARD 3: Hall of Fame */}
        <div className="bg-gray-800 p-6 rounded-2xl border border-yellow-500/50 shadow-[0_0_20px_rgba(234,179,8,0.1)] hover:border-yellow-500 transition-all duration-300 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-yellow-500/10 rounded-bl-full -mr-10 -mt-10 group-hover:bg-yellow-500/20 transition-all"></div>
          <h3 className="text-gray-400 text-sm font-bold uppercase tracking-wider mb-2">🏆 Masterpieces (Cofre)</h3>
          <div className="flex items-end gap-4">
            <span className="text-5xl font-black text-white">{summary.hall_of_fame}</span>
            <span className="text-yellow-400 font-medium mb-1">Campanhas de Ouro</span>
          </div>
          <div className="mt-6 text-sm text-gray-400 bg-gray-900/50 p-3 rounded-lg">
            Campanhas completas perfeitamente equilibradas e prontas a publicar.
          </div>
        </div>

      </div>

      {/* MENSAGEM DE ESTATUTO INFERIOR */}
      <div className="mt-8 bg-gray-900/80 border border-gray-700 p-6 rounded-xl text-center">
        <p className="text-gray-300 text-lg">
          O teu estúdio já simulou <span className="text-white font-bold">{summary.evolution.total_generations}</span> partidas diferentes
          e alcançou a vitória Humana <span className="text-green-400 font-bold">{summary.player.wins} vezes</span>.
          Continua a deixar o Bot treinar para encontrares novas Masterpieces!
        </p>
      </div>
    </div>
  );
}