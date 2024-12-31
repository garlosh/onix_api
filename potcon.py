from flask import Flask, request, jsonify
from sqlalchemy import text
from classes import pathcon
from classes import sqlHandler
from utils import calcular_tempo_total_jogador, log_regression, convert_to_geometry
from random import choice
import json
# Configuração do Flask
app = Flask(__name__)

# Configuração do SQLHandler e RCON
sql_con = sqlHandler.Client(
    'mysql', 'pymysql', 'adm', 'cabeca0213', '127.0.0.1', '3306', 'projeto_onix')
path_rcon_client = pathcon.client('127.0.0.1', 7779, 'Cucetinha')

# Carregar configurações
with open('config.json') as json_file:
    ancient_stats = json.load(json_file)

sql_con.get_table_metadata("respawns")
sql_con.get_table_metadata("ancioes")


@app.route('/pot/respawn', methods=['POST'])
def respawn():
    min_time, max_time = 8.0, 45.0
    data = request.get_json()

    player_name = data['PlayerName']
    alderon_id = data['PlayerAlderonId']
    dinosaur = data['CharacterName']
    dinosaur_id = data['CharacterID']
    growth = data['DinosaurGrowth']
    server_guid = data['ServerGuid']

    # Obter metadados da tabela respawns

    respawns_table = sql_con.TABLES["respawns"]

    # Inserir respawn
    insert_respawn = respawns_table.insert().values(
        server_guid=server_guid,
        id_alderon=alderon_id,
        nome_player=player_name,
        id_dino=dinosaur_id,
        nome_dino=dinosaur
    )
    sql_con.execute_query(insert_respawn)

    # Calcular tempo total jogado
    time_played = calcular_tempo_total_jogador(
        sql_con, alderon_id, dinosaur_id) / 3600

    # Consultar ancião normal

    ancioes_table = sql_con.TABLES["ancioes"]

    normal_ancient_query = ancioes_table.select().where(
        (ancioes_table.c.id_alderon == alderon_id) &
        (ancioes_table.c.id_dino == dinosaur_id) &
        (ancioes_table.c.tipo_anciao == 'normal')
    )
    normal_ancient = sql_con.query_database(normal_ancient_query)

    if not normal_ancient.empty:
        ancient = normal_ancient.iloc[0]
        stat = ancient['stat1']
        min_attr, max_attr = ancient_stats[stat]['min'], ancient_stats[stat]['max']
        stat_increase = log_regression(
            min_time, min_attr, max_time, max_attr, time_played)
        path_rcon_client.execute_rcommand(
            f"modattr {alderon_id} {stat} {stat_increase:.2f}")
        path_rcon_client.execute_rcommand(
            "systemmessageall Um dinosauro ancião conectou no servidor!")
    elif growth == 1.0 and time_played > min_time:
        stat = choice(list(ancient_stats.keys()))
        min_attr = ancient_stats[stat]['min']
        insert_anciao = ancioes_table.insert().values(
            id_alderon=alderon_id,
            nome_player=player_name,
            id_dino=dinosaur_id,
            nome_dino=dinosaur,
            stat1=stat,
            tipo_anciao='normal'
        )
        sql_con.execute_query(insert_anciao)
        path_rcon_client.execute_rcommand(
            f"modattr {alderon_id} {stat} {min_attr}")
        path_rcon_client.execute_rcommand(
            "systemmessageall Um dinosauro ancião conectou no servidor!")

    # Consultar ancião especial
    special_ancient_query = ancioes_table.select().where(
        (ancioes_table.c.id_alderon == alderon_id) &
        (ancioes_table.c.tipo_anciao == 'especial')
    )
    special_ancient = sql_con.query_database(special_ancient_query)

    if not special_ancient.empty:
        special = special_ancient.iloc[0]
        for stat_key in ['stat1', 'stat2']:
            stat = special[stat_key]
            min_attr, max_attr = ancient_stats[stat]['min'], ancient_stats[stat]['max']
            stat_increase = log_regression(
                min_time, min_attr, max_time, max_attr, time_played)
            path_rcon_client.execute_rcommand(
                f"modattr {alderon_id} {stat} {stat_increase:.2f}")

        path_rcon_client.execute_rcommand(
            "systemmessageall Um dinosauro ancião conectou no servidor!")

    return 'Success', 200


@app.route('/pot/leave', methods=['POST'])
def leave():
    data = request.get_json()
    alderon_id = data['PlayerAlderonId']

    # Atualizar logout
    respawns_table = sql_con.TABLES["respawns"]
    update_logout = respawns_table.update().where(
        respawns_table.c.id_alderon == alderon_id
    ).values(data_logout=text("NOW()"))

    sql_con.execute_query(update_logout)
    return 'Success', 200


@app.route('/pot/killed', methods=['POST'])
def killed():
    data = request.get_json()
    victim = data['VictimCharacterName']
    alderon_id = data['VictimAlderonId']
    nome_player = data['VictimName']

    ancioes_table = sql_con.TABLES["ancioes"]
    respawns_table = sql_con.TABLES["respawns"]

    # Remover ancião normal
    delete_anciao = ancioes_table.delete().where(
        (ancioes_table.c.id_alderon == alderon_id) &
        (ancioes_table.c.nome_player == nome_player) &
        (ancioes_table.c.nome_dino == victim) &
        (ancioes_table.c.tipo_anciao == 'normal')
    )
    sql_con.execute_query(delete_anciao)

    # Remover respawn correspondente
    delete_respawn = respawns_table.delete().where(
        (respawns_table.c.id_alderon == alderon_id) &
        (respawns_table.c.nome_player == nome_player) &
        (respawns_table.c.nome_dino == victim)
    )
    sql_con.execute_query(delete_respawn)

    return 'Success', 200


@app.route('/pot/login', methods=['POST'])
def login():
    data = request.get_json()

    # Obter metadados da tabela jogadores
    sql_con.get_table_metadata("jogadores")
    jogadores_table = sql_con.TABLES["jogadores"]

    # Inserir ou ignorar dados do jogador
    insert_jogador = jogadores_table.insert().prefix_with('IGNORE').values(
        id_alderon=data["AlderonId"],
        server_guid=data["ServerGuid"],
        server_name=data["ServerName"],
        player_name=data["PlayerName"]
    )

    sql_con.execute_query(insert_jogador)

    return "Sucesso", 200


@app.route('/pot/server_start', methods=['POST'])
def server_start():
    # Comando RCON para iniciar o modo de criador
    path_rcon_client.execute_rcommand("loadcreatormode 1")

    return "Sucesso", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=7001)
