from classes import sqlHandler
import numpy as np
import re


def log_regression(x1, y_min, x2, y_max, val):
    """
    Retorna uma função logarítmica que passa pelos pontos (x1, y_min) e (x2, y_max).

    Args:
        x1 (float): Ponto inicial no eixo x.
        y_min (float): Valor mínimo da função em x1.
        x2 (float): Ponto final no eixo x.
        y_max (float): Valor máximo da função em x2.

    Returns:
        function: Uma função logarítmica configurada.
    """
    # Calcular os parâmetros a e b
    a = (y_max - y_min) / (np.log(x2) - np.log(x1))
    b = y_min - a * np.log(x1)

    # Retornar a função logarítmica

    return min(a * np.log(val) + b, y_max)


def calcular_tempo_total_jogador(client: sqlHandler.Client, player_id: str, dino: str) -> float:
    """
    Calcula o tempo total (em segundos) que o jogador ficou no servidor,
    a partir da soma das diferenças entre login_time e logout_time (MySQL).
    """
    query = f'''SELECT
                SUM(TIMESTAMPDIFF(SECOND, data_login, data_logout)) AS total_segundos
            FROM respawns
            WHERE id_alderon = '{player_id}' AND id_dino = '{dino}' '''

    df_result = client.query_database(query)

    # Caso não haja registro no DataFrame ou esteja vazio, retorna 0
    if df_result.empty or df_result.iloc[0]['total_segundos'] is None:
        return 0.0

    total_segundos = df_result.iloc[0]['total_segundos']
    return float(total_segundos)


def convert_to_geometry(location: str) -> str:
    """
    Converte uma string no formato '(X=...,Y=...,Z=...)'
    para o formato 'GEOMETRY' utilizado pelo MySQL.

    Args:
        location (str): String com as coordenadas no formato '(X=...,Y=...,Z=...)'.

    Returns:
        str: String formatada como 'GEOMETRY' para inserção no MySQL, ex: 'POINT(X Y Z)'.
    """
    match = re.match(r"\(X=([\d.-]+),Y=([\d.-]+),Z=([\d.-]+)\)", location)
    if match:
        x, y, z = map(float, match.groups())
        return f"POINT({x} {y} {z})"
    raise ValueError(
        "Formato de localização inválido. Esperado '(X=...,Y=...,Z=...)'")
