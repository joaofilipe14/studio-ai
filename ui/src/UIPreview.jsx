import React, { useState } from 'react';

export default function UIPreview() {
  const [screen, setScreen] = useState('MainMenu');

  return (
    <div className="flex flex-col h-full animate-fade-in">
      <div className="flex justify-between items-center mb-6">
        <div>
            <h2 className="text-4xl font-bold text-cyan-400 tracking-wide">📺 Simulador de Interface</h2>
            <p className="text-gray-400 mt-2">Tradução em tempo real do Unity Toolkit (UXML) para a Web.</p>
        </div>

        <select
          value={screen}
          onChange={(e) => setScreen(e.target.value)}
          className="bg-gray-800 text-white px-6 py-3 rounded-xl border-2 border-cyan-700 outline-none focus:border-cyan-400 text-lg font-bold shadow-[0_0_15px_rgba(6,182,212,0.3)] cursor-pointer"
        >
          <option value="MainMenu">🏠 Menu Principal</option>
          <option value="VaultScreen">🏦 O Cofre (Loja)</option>
          <option value="HUD">🏃 HUD In-Game</option>
        </select>
      </div>

      {/* A moldura do Simulador */}
      <div className="flex-1 border-4 border-gray-700 rounded-2xl overflow-hidden shadow-2xl relative bg-black">
         <iframe
            src={`http://localhost:8000/ui/preview/${screen}`}
            className="w-full h-full border-none"
            title="UI Preview"
         />
      </div>
    </div>
  );
}