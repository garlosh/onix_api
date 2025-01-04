from flask import Flask, request, jsonify
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common import pathcon

app = Flask(__name__)
path_rcon_client = pathcon.client('127.0.0.1', 7779, 'Cucetinha')
AUTH_PASSWORD = "ZYY41296zdQYO3ANGd84BitEfzCS7zwnnpsfs6T2ZJH4QqfixH"


def check_auth(password):
    """Verifica se a senha fornecida é válida."""
    return password == AUTH_PASSWORD


@app.route('/pot/rcon_protegido', methods=['POST'])
def rcon_protegido():
    """Rota protegida que exige autenticação."""
    auth_header = request.headers.get('Authorization')

    # Verifica se o cabeçalho Authorization está presente
    if not auth_header:
        return jsonify({"message": "Autenticação necessária"}), 401

    # A senha é esperada no formato "Bearer <password>"
    try:
        scheme, password = auth_header.split(" ")
        if scheme != "Bearer":
            raise ValueError("Formato de autenticação inválido")
    except ValueError:
        return jsonify({"message": "Formato de autenticação inválido"}), 400

    # Verifica a senha
    if not check_auth(password):
        return jsonify({"message": "Senha inválida"}), 403

    # Se a autenticação for bem-sucedida, processa os dados do POST
    data = request.json
    if not data:
        return jsonify({"message": "Nenhum dado enviado"}), 400

    try:
        response = path_rcon_client.execute_rcommand(data['command'])
    except Exception as e:
        return jsonify({"message": e}), 500

    # Retorna os dados recebidos como exemplo de resposta
    return jsonify({
        "message": response,
        "data_received": data
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=7002)
