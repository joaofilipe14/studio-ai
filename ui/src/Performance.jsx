import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine
} from 'recharts';

export default function Performance() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = () => {
    fetch('http://localhost:8000/performance/metrics')
      .then(res => res.json())
      .then(json => {
        // O backend manda os mais recentes primeiro.
        // Para o gráfico, queremos a ordem cronológica (da esquerda para a direita)
        const reversedData = (json.data || []).reverse().map(d => ({
          ...d,
          // Convertemos para percentagem para o gráfico ficar bonito (0 a 100)
          winRatePercent: d.win_rate * 100,
          generation: `Gen ${d.id}`
        }));
        setData(reversedData);
        setLoading(false);
      })
      .catch(err => {
        console.error("Erro a carregar métricas:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="text-yellow-500 text-xl font-bold animate-pulse">A ligar ao Cérebro Central... 🧠</div>;

  // Para a tabela, voltamos a inverter para ver os mais recentes no topo
  const tableData = [...data].reverse();

  // Custom Tooltip para o Gráfico com o aspeto Cyberpunk
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const run = payload[0].payload;
      return (
        <div className="bg-gray-900 border border-gray-700 p-4 rounded-lg shadow-xl">
          <p className="font-bold text-yellow-500 mb-2">{label} (Lvl {run.level_id})</p>
          <p className="text-sm text-white">Jogador: {run.is_human ? '🧑 Humano' : '🤖 Bot'}</p>
          <p className="text-sm text-green-400">Win Rate: {run.winRatePercent.toFixed(0)}%</p>
          <p className="text-sm text-red-400">Inimigos: {run.enemy_count} (Vel: {run.enemy_speed.toFixed(1)})</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="animate-fade-in text-white space-y-8">
      <div className="flex justify-between items-center">
        <h2 className="text-4xl font-bold text-yellow-500 tracking-wide">📈 MÉTRICAS DE EVOLUÇÃO</h2>
        <button onClick={fetchMetrics} className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded text-sm transition">
          🔄 Atualizar Agora
        </button>
      </div>

      {data.length === 0 ? (
        <div className="bg-gray-800 p-8 rounded-xl border border-gray-700 text-center text-gray-400">
          Ainda não há dados de simulação. Põe o Runner a trabalhar! 🏃‍♂️
        </div>
      ) : (
        <>
          {/* ========================================= */}
          {/* ZONA DO GRÁFICO (RECHARTS)                */}
          {/* ========================================= */}
          <div className="bg-gray-800 p-6 rounded-2xl border border-gray-700 shadow-xl">
            <h3 className="text-xl font-bold text-gray-300 mb-6">📉 Evolução do Equilíbrio (Win Rate vs Dificuldade)</h3>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="generation" stroke="#9CA3AF" fontSize={12} />

                  {/* Eixo Esquerdo (Win Rate) */}
                  <YAxis yAxisId="left" stroke="#4ADE80" domain={[0, 100]} label={{ value: 'Win Rate (%)', angle: -90, position: 'insideLeft', fill: '#4ADE80' }} />

                  {/* Eixo Direito (Velocidade do Inimigo) */}
                  <YAxis yAxisId="right" orientation="right" stroke="#F87171" domain={[0, 10]} label={{ value: 'Velocidade Inimigo', angle: 90, position: 'insideRight', fill: '#F87171' }} />

                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ paddingTop: "20px" }} />

                  {/* Linhas do Gráfico */}
                  <Line yAxisId="left" type="monotone" dataKey="winRatePercent" name="Win Rate %" stroke="#4ADE80" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 8 }} />
                  <Line yAxisId="right" type="monotone" dataKey="enemy_speed" name="Velocidade Inimigo" stroke="#F87171" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 3 }} />

                  {/* Sweet Spot Reference Line (O ideal é entre 60% e 80%) */}
                  <ReferenceLine yAxisId="left" y={60} stroke="#EAB308" strokeDasharray="3 3" opacity={0.5} />
                  <ReferenceLine yAxisId="left" y={80} stroke="#EAB308" strokeDasharray="3 3" opacity={0.5} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-center text-gray-500 mt-4">A zona ideal (Sweet Spot) para a IA é manter o Win Rate entre as linhas amarelas pontilhadas (60% - 80%).</p>
          </div>

          {/* ========================================= */}
          {/* TABELA DE HISTÓRICO (DADOS CRUS)          */}
          {/* ========================================= */}
          <div className="bg-gray-800 rounded-2xl border border-gray-700 shadow-xl overflow-hidden overflow-x-auto">
            <table className="w-full text-left border-collapse whitespace-nowrap">
              <thead>
                <tr className="border-b border-gray-700 bg-gray-900/50 text-gray-400 uppercase text-xs tracking-wider">
                  <th className="py-4 px-6 font-medium">Geração</th>
                  <th className="py-4 px-6 font-medium text-center">Nível</th>
                  <th className="py-4 px-6 font-medium text-center">Jogador</th>
                  <th className="py-4 px-6 font-medium">Win Rate</th>
                  <th className="py-4 px-6 font-medium">Dificuldade</th>
                  <th className="py-4 px-6 font-medium">Relatório da IA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/50">
                {tableData.map((entry) => {
                  const winColor = entry.win_rate >= 0.8 ? 'bg-green-500' : entry.win_rate >= 0.4 ? 'bg-yellow-500' : 'bg-red-500';

                  return (
                    <tr key={entry.id} className="hover:bg-gray-700/30 transition duration-150">
                      <td className="py-4 px-6 text-sm text-gray-400 font-mono">
                        <span className="text-white font-bold mr-2">#{entry.id}</span>
                        {entry.timestamp.replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/, '$4:$5:$6')}
                      </td>

                      <td className="py-4 px-6 font-bold text-center">
                        <span className="bg-blue-900/40 text-blue-400 px-3 py-1 rounded-full text-sm">Lvl {entry.level_id}</span>
                      </td>

                      <td className="py-4 px-6 text-center">
                         <span className={`px-3 py-1 rounded text-xs font-bold uppercase tracking-wider ${entry.is_human ? 'bg-green-900/60 text-green-400 border border-green-700' : 'bg-purple-900/60 text-purple-400 border border-purple-700'}`}>
                           {entry.is_human ? 'Humano 👤' : 'Bot 🤖'}
                         </span>
                      </td>

                      <td className="py-4 px-6">
                        <div className="flex items-center gap-3">
                          <div className="w-24 h-2.5 bg-gray-900 rounded-full overflow-hidden shadow-inner">
                            <div className={`h-full ${winColor}`} style={{ width: `${Math.max(entry.win_rate * 100, 5)}%` }}></div>
                          </div>
                          <span className="text-sm font-bold w-12 text-right">{(entry.win_rate * 100).toFixed(0)}%</span>
                        </div>
                      </td>

                      <td className="py-4 px-6 text-sm text-gray-300">
                        👾 <span className="text-red-400 font-bold">{entry.enemy_count}</span> |
                        💨 <span className="text-yellow-400 font-bold">{entry.enemy_speed.toFixed(1)}</span> |
                        🧱 <span className="text-orange-400 font-bold">{entry.obstacles}</span>
                      </td>

                      <td className="py-4 px-6 text-xs text-gray-400 max-w-xs truncate cursor-help" title={entry.report}>
                        {entry.report}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}