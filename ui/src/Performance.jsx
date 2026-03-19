import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, AreaChart, Area
} from 'recharts';

export default function Performance() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Estados dos Filtros
  const [playerFilter, setPlayerFilter] = useState('all');
  const [sessionFilter, setSessionFilter] = useState('all');

  useEffect(() => {
    fetch('http://localhost:8000/performance/metrics')
      .then(res => {
        if (!res.ok) throw new Error('Falha ao carregar as métricas');
        return res.json();
      })
      .then(json => {
        const actualData = json.data ? json.data : json;
        setData(actualData);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="text-white p-4 flex justify-center items-center h-screen">A carregar telemetria...</div>;
  if (error) return <div className="text-red-400 p-4">Erro: {error}</div>;
  if (data.length === 0) return <div className="text-white p-4">Sem dados para exibir.</div>;

  const uniqueSessions = [...new Set(data.map(item => item.session_id))].filter(Boolean);

  // Filtrar e Processar os dados para extrair as métricas extra do JSON (se existirem)
  const filteredData = data.filter(row => {
    let matchesPlayer = true;
    if (playerFilter === 'human') matchesPlayer = row.is_human === true || row.is_human === 1 || row.is_human === "true";
    if (playerFilter === 'bot') matchesPlayer = row.is_human === false || row.is_human === 0 || row.is_human === "false";

    let matchesSession = true;
    if (sessionFilter !== 'all') matchesSession = row.session_id === sessionFilter;

    return matchesPlayer && matchesSession;
  }).map(row => {
    // Tenta extrair as métricas detalhadas do "raw_metrics" caso o backend envie
    let lives_lost = 0;
    let timeouts = 0;
    let collected_coins = 0;
    let powerups_used = 0;

    try {
      if (row.raw_metrics) {
        const parsed = JSON.parse(row.raw_metrics);
        const report = parsed.level_reports?.find(r => r.level_id === row.level_id) || {};
        lives_lost = report.lives_lost || 0;
        timeouts = report.timeouts || 0;
        collected_coins = report.collected_coins || 0;
        powerups_used = report.powerups_used || 0;
      }
    } catch (e) { console.warn("Erro ao ler raw_metrics da linha", row.id); }

    return {
      ...row,
      win_rate_percent: Math.round(row.win_rate * 100), // Converte 0.5 para 50%
      lives_lost,
      timeouts,
      collected_coins,
      powerups_used
    };
  });

  return (
    <div className="p-6 bg-gray-900 min-h-screen">
      <div className="flex justify-between items-center mb-6 border-b border-gray-700 pb-4">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">Evolução & Telemetria</h2>
          <p className="text-gray-400 mt-1">Analisa o Flow e a Dificuldade do teu Level Design</p>
        </div>

        {/* Painel de Filtros */}
        <div className="flex space-x-4">
          <select
            className="bg-gray-800 text-white p-2 rounded border border-gray-600 outline-none focus:border-blue-500 shadow-sm"
            value={playerFilter}
            onChange={e => setPlayerFilter(e.target.value)}
          >
            <option value="all">Todos os Jogadores</option>
            <option value="human">Apenas Humano</option>
            <option value="bot">Apenas Bot (IA)</option>
          </select>

          <select
            className="bg-gray-800 text-white p-2 rounded border border-gray-600 outline-none focus:border-blue-500 shadow-sm"
            value={sessionFilter}
            onChange={e => setSessionFilter(e.target.value)}
          >
            <option value="all">Todas as Sessões</option>
            {uniqueSessions.map(session => (
              <option key={session} value={session}>{session}</option>
            ))}
          </select>
        </div>
      </div>

      {filteredData.length === 0 ? (
        <div className="text-gray-400 py-10 text-center text-lg">Nenhum dado encontrado para os filtros selecionados.</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

          {/* GRÁFICO 1: Curva de Dificuldade (Velocidade vs Obstáculos) */}
          <div className="bg-gray-800 p-4 rounded-xl shadow-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4 text-center">1. Curva de Dificuldade</h3>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={filteredData} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="level_id" stroke="#9CA3AF" />
                  <YAxis yAxisId="left" stroke="#60A5FA" />
                  <YAxis yAxisId="right" orientation="right" stroke="#F87171" />
                  <Tooltip contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#fff' }} labelFormatter={(v) => `Nível ${v}`} />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="enemy_speed" name="Vel. Inimigos" stroke="#60A5FA" strokeWidth={3} dot={{ r: 3 }} />
                  <Line yAxisId="right" type="monotone" dataKey="obstacles" name="Obstáculos" stroke="#F87171" strokeWidth={3} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* GRÁFICO 2: Taxa de Sobrevivência (Win Rate) */}
          <div className="bg-gray-800 p-4 rounded-xl shadow-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4 text-center">2. Taxa de Sobrevivência (Win Rate %)</h3>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={filteredData} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="level_id" stroke="#9CA3AF" />
                  <YAxis domain={[0, 100]} stroke="#34D399" />
                  <Tooltip contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#fff' }} labelFormatter={(v) => `Nível ${v}`} />
                  <Legend />
                  <Bar dataKey="win_rate_percent" name="Win Rate (%)" fill="#34D399" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* GRÁFICO 3: Causas de Morte (Vidas vs Timeouts) */}
          <div className="bg-gray-800 p-4 rounded-xl shadow-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4 text-center">3. Análise de Frustração (Mortes)</h3>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={filteredData} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="level_id" stroke="#9CA3AF" />
                  <YAxis stroke="#FBBF24" />
                  <Tooltip contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#fff' }} labelFormatter={(v) => `Nível ${v}`} />
                  <Legend />
                  <Area type="monotone" dataKey="lives_lost" name="Apanhado por Inimigo" stackId="1" stroke="#EF4444" fill="#EF4444" opacity={0.8} />
                  <Area type="monotone" dataKey="timeouts" name="Falta de Tempo" stackId="1" stroke="#F59E0B" fill="#F59E0B" opacity={0.8} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* GRÁFICO 4: O "Fun Meter" (Moedas e Power-Ups) */}
          <div className="bg-gray-800 p-4 rounded-xl shadow-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4 text-center">4. Medidor de Exploração (Fun Meter)</h3>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={filteredData} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="level_id" stroke="#9CA3AF" />
                  <YAxis stroke="#A855F7" />
                  <Tooltip contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#fff' }} labelFormatter={(v) => `Nível ${v}`} />
                  <Legend />
                  <Bar dataKey="collected_coins" name="Moedas Apanhadas" fill="#FCD34D" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="powerups_used" name="Power-Ups Usados" fill="#A855F7" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>
      )}
    </div>
  );
}