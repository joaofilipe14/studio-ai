import React, { useState } from 'react';
import Home from './Home';
import Vault from './Vault';
import MarketingHub from './Marketing';
import AudioStudio from './Audio';
import ArtStudio from './Art';
import Performance from './Performance';
import HallOfFame from './HallOfFame';
import UIPreview from './UIPreview';

export default function App() {
  const [activePage, setActivePage] = useState('home');
  const [toast, setToast] = useState(null);
  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const menuItems = [
    { id: 'home', label: '🏠 Dashboard' },
    { id: 'performance', label: '📈 Performance' },
    { id: 'hall', label: '🏆 Hall of Fame' },
    { id: 'art', label: '🎨 Estúdio de Arte' },
    { id: 'audio', label: '🎵 Sonoplastia' },
    { id: 'marketing', label: '🚀 Marketing Hub' },
    { id: 'vault', label: '🏦 O Cofre' },
    { id: 'uipreview', label: '📺 Simulador UI' }
  ];

  return (
    <div className="flex h-screen bg-gray-900 text-white font-sans overflow-hidden relative">

      {/* 🚨 3. O BALÃO TOAST RENDERIZADO GLOBALMENTE (Por cima de tudo) */}
      {toast && (
        <div className={`fixed top-6 right-6 px-6 py-4 rounded-xl shadow-2xl border-2 z-50 text-white font-bold transition-all transform animate-fade-in ${
            toast.type === "success"
                ? "bg-green-900 border-green-500 shadow-[0_0_15px_rgba(34,197,94,0.5)]"
                : "bg-red-900 border-red-500 shadow-[0_0_15px_rgba(239,68,68,0.5)]"
        }`}>
            {toast.type === "success" ? "✅ " : "⚠️ "} {toast.message}
        </div>
      )}

      {/* BARRA LATERAL (SIDEBAR) */}
      <div className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col z-10">
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
      <div className="flex-1 overflow-y-auto p-8 z-0">
        {/* 🚨 4. PASSAMOS A FUNÇÃO 'showToast' PARA AS PÁGINAS COMO UMA "PROP" */}
        {activePage === 'home' && <Home showToast={showToast} />}
        {activePage === 'performance' && <Performance showToast={showToast} />}
        {activePage === 'hall' && <HallOfFame showToast={showToast} />}
        {activePage === 'art' && <ArtStudio showToast={showToast} />}
        {activePage === 'audio' && <AudioStudio showToast={showToast} />}
        {activePage === 'marketing' && <MarketingHub showToast={showToast} />}
        {activePage === 'vault' && <Vault showToast={showToast} />}
        {activePage === 'uipreview' && <UIPreview showToast={showToast} />}
      </div>

    </div>
  );
}