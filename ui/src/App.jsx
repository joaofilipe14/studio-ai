import React, { useState } from 'react';
import Home from './Home';
import Vault from './Vault';
import MarketingHub from './Marketing';
import AudioStudio from './Audio';
import ArtStudio from './Art';
import Performance from './Performance';
// Não te esqueças de importar também o Hall of Fame se já o tiveres criado!
import HallOfFame from './HallOfFame';

export default function App() {
  // 🎯 1. AQUI: Começa a app na aba 'home' em vez de 'marketing'
  const [activePage, setActivePage] = useState('home');

  // 🎯 2. AQUI: Adiciona os botões da Home e do Hall of Fame ao menu
  const menuItems = [
    { id: 'home', label: '🏠 Dashboard' },              // <--- NOVO
    { id: 'performance', label: '📈 Performance' },
    { id: 'hall', label: '🏆 Hall of Fame' },           // <--- NOVO
    { id: 'art', label: '🎨 Estúdio de Arte' },
    { id: 'audio', label: '🎵 Sonoplastia' },
    { id: 'marketing', label: '🚀 Marketing Hub' },
    { id: 'vault', label: '🏦 O Cofre' }
  ];

  return (
    <div className="flex h-screen bg-gray-900 text-white font-sans overflow-hidden">

      {/* BARRA LATERAL (SIDEBAR) */}
      <div className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-cyan-400 tracking-wider">🎮 Studio-AI</h1>
          <p className="text-xs text-gray-400 mt-1">Master Control</p>
        </div>

        <nav className="flex-1 px-4 space-y-2 mt-4">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActivePage(item.id)}
              className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors duration-200 ${
                activePage === item.id
                  ? 'bg-cyan-900/50 text-cyan-300 border border-cyan-700/50'
                  : 'text-gray-400 hover:bg-gray-700 hover:text-gray-200'
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="p-6 border-t border-gray-700">
          <h3 className="text-xs uppercase text-gray-500 font-semibold mb-2">⚙️ Status do Sistema</h3>
          <div className="flex items-center text-sm">
            <span className="h-2 w-2 rounded-full bg-green-500 mr-2"></span>
            Diretor IA (Ollama)
          </div>
          <div className="flex items-center text-sm mt-1">
            <span className="h-2 w-2 rounded-full bg-green-500 mr-2"></span>
            API Gateway
          </div>
        </div>
      </div>

      {/* ÁREA DE CONTEÚDO PRINCIPAL */}
      <div className="flex-1 overflow-y-auto p-8">
        {/* 🎯 3. As tuas rotas internas */}
        {activePage === 'home' && <Home />}
        {activePage === 'performance' && <Performance />}
        {activePage === 'hall' && <HallOfFame />}
        {activePage === 'art' && <ArtStudio />}
        {activePage === 'audio' && <AudioStudio />}
        {activePage === 'marketing' && <MarketingHub />}
        {activePage === 'vault' && <Vault />}
      </div>

    </div>
  );
}