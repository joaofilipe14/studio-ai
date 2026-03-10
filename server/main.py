# server/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importas os teus routers separados
from server.routes import player, director, marketing, audio, art, performance

app = FastAPI(title="Studio-AI Central API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔌 "Ligas" os routers à tua API principal
app.include_router(performance.router)
app.include_router(audio.router)
app.include_router(art.router)
app.include_router(marketing.router)
app.include_router(player.router)
app.include_router(director.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)