from flask import Flask, request
from classes import sqlHandler
from classes import pathcon
import numpy as np
from random import choice
app = Flask(__name__)
sql_con_logins = sqlHandler.Client('mysql', 'pymysql', 'adm',
                                   'cabeca0213', '127.0.0.1', '3306', 'projeto_onix', 'logins')
sql_con_ancioes = sqlHandler.Client('mysql', 'pymysql', 'adm',
                                    'cabeca0213', '127.0.0.1', '3306', 'projeto_onix', 'ancioes')
path_rcon_client = pathcon.client('127.0.0.1', 7779, 'Cucetinha')
ancient_stats = {'MaxHealth': {'min': 10, 'max': 50}, 'Armor': {'min': 0.01, 'max': 0.05},
                 'CombatWeight': {'min': 100, 'max': 325}, 'MaxStamina': {'min': 5, 'max': 15}}


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

    return a * np.log(val) + b


def calcular_tempo_total_jogador(client: sqlHandler.Client, player_id: str) -> float:
    """
    Calcula o tempo total (em segundos) que o jogador ficou no servidor,
    a partir da soma das diferenças entre login_time e logout_time (MySQL).
    """
    query = f'''SELECT
                SUM(TIMESTAMPDIFF(SECOND, data_login, data_logout)) AS total_segundos
            FROM logins
            WHERE id_alderon = '{player_id}' '''

    df_result = client.query_database(query)

    # Caso não haja registro no DataFrame ou esteja vazio, retorna 0
    if df_result.empty or df_result.iloc[0]['total_segundos'] is None:
        return 0.0

    total_segundos = df_result.iloc[0]['total_segundos']
    return float(total_segundos)


@app.route('/pot/respawn', methods=['POST'])
def respawn():
    min_time = 15.0
    max_time = 45.0

    # Pega os dados do webhook
    data = request.get_json()
    player_name = data['PlayerName']
    alderon_id = data['PlayerAlderonId']
    dinosaur = data['CharacterName']
    growth = data['DinosaurGrowth']

    # Insere o login no sql
    sql_con_logins.execute_query(f'''INSERT INTO logins (id_alderon, nome_player, nome_dino)
                            VALUES ('{alderon_id}', '{player_name}', '{dinosaur}'); ''')

    # Calcula o tempo e verifica se já é ancião
    time_played = calcular_tempo_total_jogador(sql_con_logins, alderon_id)/3600
    flag_ancient = sql_con_ancioes.query_database(
        f'''SELECT * FROM ancioes WHERE id_alderon = '{alderon_id}' ''')
    if not flag_ancient.empty:
        min_attr = ancient_stats[flag_ancient['stat']]['min']
        max_attr = ancient_stats[flag_ancient['stat']]['max']
        stat_increase = min_attr + log_regression(
            min_time, 0, max_time, max_attr, time_played)
        path_rcon_client.execute_rcommand(
            f'modattr {alderon_id} {flag_ancient['stat']} {stat_increase:.2f}')
        path_rcon_client.execute_rcommand(
            f'announce Um dinosauro anci\u00c2o conectou no servidor!')
    elif growth == 1.0 and time_played > min_time:
        stat_aleatorio = choice(list(ancient_stats.keys()))
        min_attr = ancient_stats[stat_aleatorio]['min']
        sql_con_logins.execute_query(f'''INSERT INTO logins (id_alderon, nome_player, nome_dino, stat, tipo_anciao)
                            VALUES ({player_name}, '{alderon_id}','{dinosaur}', '{stat_aleatorio}', 'normal'); ''')
        path_rcon_client.execute_rcommand(
            f'modattr {alderon_id} {stat_aleatorio} {min_attr}')
        path_rcon_client.execute_rcommand(
            f'announce Um dinosauro anci\u00c2o conectou no servidor!')


@app.route('/pot/leave', methods=['POST'])
def leave():
    data = request.get_json()
    alderon_id = data['PlayerAlderonId']
    sql_con_logins.execute_query(f'''
                        UPDATE logins
                        SET data_logout = NOW()
                        WHERE id = '{alderon_id}';
                        ''')


@app.route('/pot/killed', methods=['POST'])
def killed():
    data = request.get_json()
    victim = data['VictimCharacterName']
    alderon_id = data['VictimAlderonId']
    nome_player = data['VictimName']
    sql_con_ancioes.execute_query(f'''
                        DELETE FROM ancioes
                        WHERE id = '{alderon_id}' AND nome_player = '{nome_player}' AND nome_dino = '{victim}' AND tipo_anciao = 'normal';
                        ''')
    sql_con_logins.execute_query(f'''
                        DELETE FROM logins
                        WHERE id = '{alderon_id}' AND nome_player = '{nome_player}' AND nome_dino = '{victim}';
                        ''')


if __name__ == '__main__':
    # run app in debug mode on port 80
    app.run(debug=True, port=80)
