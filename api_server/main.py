from fastapi import FastAPI
from random import choice
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from api_server.router import players

# Configuração do FastAPI
app = FastAPI()
app.include_router(players.router)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=7001, log_level="info")
