import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function HallOfFame() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);

  // 🎯 NOVO ESTADO: Guarda qual a campanha que clicaste
  const [selectedCampaign, setSelectedCampaign] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/hall_of_fame/compare')
      .then(res => res.json())
      .then(json => {
        setCampaigns(json.data || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Erro ao carregar Hall of Fame:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="text-yellow-500 text-xl font-bold animate-pulse">A abrir o Cofre Dourado... 🏆</div>;

  // Transformar os dados para o gráfico ler múltiplas campanhas ao mesmo tempo
  const chartData = [];
  for (let i = 0; i < 10; i++) {
    const levelRow = { level: `Nível ${i + 1}` };
    campaigns.forEach(camp => {
      if (camp.levels[i]) {
        levelRow[camp.id] = camp.levels[i].difficulty;
      }
    });
    chartData.push(levelRow);
  }

  // 🎯 LÓGICA DE FILTRO: Se selecionaste um, mostra só esse. Senão, mostra os últimos 5.
  const campaignsToShow = selectedCampaign
    ? campaigns.filter(c => c.id === selectedCampaign)
    : campaigns.slice(0, 5);

  const colors = ['#F59E0B', '#3B82F6', '#10B981', '#EC4899', '#8B5CF6'];

  return (
    <div className="animate-fade-in text-white space-y-8">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-4xl font-bold text-yellow-500 tracking-wide">🏆 HALL OF FAME</h2>
          <p className="text-gray-400 mt-2">Clica num cartão abaixo para isolar a sua curva de dificuldade no gráfico.</p>
        </div>
      </div>

      {campaigns.length === 0 ? (
        <div className="bg-gray-800 p-8 rounded-xl border border-gray-700 text-center text-gray-400">
          Nenhuma campanha mestre encontrada. O Bot ainda está a suar! 🤖💦
        </div>
      ) : (
        <>
          <div className="bg-gray-800 p-6 rounded-2xl border border-gray-700 shadow-xl transition-all">
            <h3 className="text-xl font-bold text-gray-300 mb-6">
              {selectedCampaign ? `📊 A analisar Campanha Isolada` : `📊 Comparação das Últimas 5 Masterpieces`}
            </h3>
            <div className="h-96 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="level" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" label={{ value: 'Índice de Ameaça', angle: -90, position: 'insideLeft', fill: '#9CA3AF' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151' }} />
                  <Legend />

                  {campaignsToShow.map((camp, index) => {
                    // 🎯 FIX DO ID: Agora usamos o bloco do tempo inteiro (6 dígitos) usando o split('-')
                    const timeId = camp.id.includes('-') ? camp.id.split('-')[1] : camp.id.substring(0, 6);

                    return (
                      <Line
                        key={camp.id}
                        type="monotone"
                        dataKey={camp.id}
                        name={`Campanha ${timeId}`} // <--- Nomes únicos no gráfico!
                        stroke={selectedCampaign ? '#F59E0B' : colors[index % colors.length]}
                        strokeWidth={selectedCampaign ? 4 : 3}
                        activeDot={{ r: 8 }}
                      />
                    );
                  })}

                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Botão para limpar a seleção se estiver um isolado */}
            {selectedCampaign && (
              <div className="mt-4 flex justify-center">
                 <button
                    onClick={() => setSelectedCampaign(null)}
                    className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg text-sm transition"
                 >
                   👁️ Mostrar Múltiplas Campanhas
                 </button>
              </div>
            )}
          </div>

          {/* GRELHA DE CARTÕES CLICÁVEIS */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {campaigns.map((camp, i) => {
              const isSelected = selectedCampaign === camp.id;

              return (
                <div
                  key={camp.id}
                  // 🎯 LÓGICA DE CLIQUE AQUI
                  onClick={() => setSelectedCampaign(isSelected ? null : camp.id)}
                  className={`bg-gray-900 border p-6 rounded-xl relative overflow-hidden group cursor-pointer transition-all duration-300 ${
                    isSelected
                      ? 'border-yellow-500 shadow-[0_0_20px_rgba(234,179,8,0.3)] scale-[1.02]'
                      : 'border-gray-700 hover:border-gray-500 hover:bg-gray-800'
                  }`}
                >
                  {i === 0 && !isSelected && (
                    <div className="absolute top-0 right-0 bg-yellow-500 text-black text-xs font-bold px-3 py-1 rounded-bl-lg z-10">
                      MAIS RECENTE
                    </div>
                  )}
                  {isSelected && (
                    <div className="absolute top-0 right-0 bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg z-10">
                      ANALISANDO
                    </div>
                  )}

                  <h4 className={`text-lg font-bold mb-2 break-all ${isSelected ? 'text-yellow-400' : 'text-blue-400'}`}>
                    {camp.id}
                  </h4>
                  <div className="space-y-2 text-sm text-gray-400">
                    <p>Dificuldade Média: <span className="text-white font-bold">{camp.avg_difficulty.toFixed(1)}</span></p>
                    <p>Inimigos Finais (Lvl 10): <span className="text-red-400 font-bold">{camp.levels[9]?.enemies || 0}</span></p>
                    <p>Velocidade Final: <span className="text-yellow-400 font-bold">{camp.levels[9]?.speed || 0}</span></p>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}