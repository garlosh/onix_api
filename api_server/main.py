from fastapi import FastAPI
from random import choice
import sys
import os
from router import players
# Import das classess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configuração do FastAPI
app = FastAPI()
app.include_router(players.router)
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=7001)
