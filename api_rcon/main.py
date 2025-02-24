from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common import pathcon

app = FastAPI()
path_rcon_client = pathcon.client('127.0.0.1', 7779, 'Cucetinha')
AUTH_PASSWORD = "ZYY41296zdQYO3ANGd84BitEfzCS7zwnnpsfs6T2ZJH4QqfixH"


def check_auth(password: str) -> bool:
    """Verifica se a senha fornecida é válida."""
    return password == AUTH_PASSWORD


@app.post('/pot/rcon_protegido')
async def rcon_protegido(request: Request):
    """Rota protegida que exige autenticação."""
    auth_header = request.headers.get('Authorization')

    # Verifica se o cabeçalho Authorization está presente
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticação necessária")

    # A senha é esperada no formato "Bearer <password>"
    try:
        scheme, password = auth_header.split(" ")
        if scheme != "Bearer":
            raise ValueError("Formato de autenticação inválido")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Formato de autenticação inválido")

    # Verifica a senha
    if not check_auth(password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Senha inválida")

    # Se a autenticação for bem-sucedida, processa os dados do POST
    data = await request.json()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum dado enviado")

    try:
        response = path_rcon_client.execute_rcommand(data['command'])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # Retorna os dados recebidos como exemplo de resposta
    return JSONResponse(content={
        "message": response,
        "data_received": data
    })


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=7002)
