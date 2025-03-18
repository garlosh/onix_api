#!/bin/bash

# Salva o diretório atual como BASE_DIR
BASE_DIR=$(pwd)

# Caminho para o ambiente virtual (venv)
VENV_DIR="$BASE_DIR/venv"

# Caminho do script Python a ser executado
PYTHON_SCRIPT="$BASE_DIR/api_server/main.py"

# Verifica se o ambiente virtual existe
if [[ -d "$VENV_DIR" ]]; then
    echo "Ativando o ambiente virtual em: $VENV_DIR"
    source "$VENV_DIR/bin/activate"
else
    echo "Erro: Ambiente virtual não encontrado em $VENV_DIR"
    exit 1
fi

# Verifica se o script Python existe
if [[ -f "$PYTHON_SCRIPT" ]]; then
    echo "Executando o script Python: $PYTHON_SCRIPT"
    python -m api_server.main
else
    echo "Erro: Script Python não encontrado em $PYTHON_SCRIPT"
    deactivate  # Desativa o venv, caso tenha sido ativado
    exit 1
fi

# Desativa o ambiente virtual após a execução
deactivate
