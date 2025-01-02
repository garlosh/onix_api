from sqlalchemy.sql import text
from flask import Flask, request
from sqlalchemy import text, select
from classes import pathcon, sqlHandler
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
sql_con.get_table_metadata("server_error")
sql_con.get_table_metadata("jogadores")
sql_con.get_table_metadata("player_report")
sql_con.get_table_metadata("admin_commands")


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
    nome_dino = data['CharacterName']

    # Tabela de respawns
    respawns_table = sql_con.TABLES["respawns"]

    # Subconsulta para obter o registro mais recente
    subquery = select(respawns_table.c.id).where(
        (respawns_table.c.id_alderon == alderon_id) &
        (respawns_table.c.nome_dino == nome_dino)
    ).order_by(respawns_table.c.data_login.desc()).limit(1)

    # Executa a subconsulta usando sql_con
    result = sql_con.execute_query(subquery)
    print(result)
    id_to_update = result.scalar() if result else None

    if id_to_update:
        # Atualizar logout do registro mais recente
        update_logout = (
            respawns_table.update()
            .where(respawns_table.c.id == id_to_update)
            .values(data_logout=text("NOW()"))
        )
        sql_con.execute_query(update_logout)
        return 'Success', 200
    else:
        return 'No matching record found', 404


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


@app.route('/pot/server_error', methods=['POST'])
def server_error():
    data = request.get_json()

    server_error_table = sql_con.TABLES["server_error"]
    # Inserir respawn
    insert_respawn = server_error_table.insert().values(
        server_guid=data['ServerGuid'],
        server_ip=data['ServerIP'],
        server_name=data['ServerName'],
        uuid=data['UUID'],
        provider=data['Provider'],
        instance=data['Instance'],
        session=data['Session'],
        error_message=data['ErrorMesssage']
    )
    sql_con.execute_query(insert_respawn)
    return "Sucesso", 200


@app.route('/pot/player_report', methods=['POST'])
def player_report():
    data = request.get_json()

    player_report_table = sql_con.TABLES['player_report']
    # Inserir respawn
    insert_report = player_report_table.insert().values(
        server_guid=data['ServerGuid'],
        reporter_player_name=data['ReporterPlayerName'],
        reporter_player_id=data['ReporterAlderonId'],
        server_name=data['ServerName'],
        reported_player_name=data['ReportedPlayerName'],
        reported_alderon_id=data['ReportedAlderonId'],
        reported_platform=data['ReportedPlatform'],
        report_type=data['ReportType'],
        report_reason=data['ReportReason'],
        recent_damage_causer_ids=data['RecentDamageCauserIDs'],
        nearby_players_id=data['NearbyPlayerIDs'],
        title=data['Title'],
        message=data['Message'],
        location=convert_to_geometry(data['Location']),
        platform=data['Platform']
    )
    sql_con.execute_query(insert_report)
    return "Sucesso", 200


@app.route('/pot/bad_average_tick', methods=['POST'])
def bad_average_tick():
    data = request.get_json()

    bad_average_tick_table = sql_con.TABLES['player_report']
    # Inserir respawn
    insert_tick = bad_average_tick_table.insert().values(
        server_guid=data['ServerGuid'],
        server_ip=data['ServerIP'],
        server_name=data['ServerName'],
        uuid=data['UUID'],
        provider=data['Provider'],
        instance=data['Instance'],
        session=data['Session'],
        average_tick_rate=data['AverageTickRate'],
        current_tick_rate=data['CurrentTickRate'],
        player_count=data['PlayerCount']
    )
    sql_con.execute_query(insert_tick)
    return "Sucesso", 200


@app.route('/pot/admin_command', methods=['POST'])
def admin_command():
    data = request.get_json()

    admin_command_table = sql_con.TABLES['admin_commands']
    # Tratar campos opcionais
    # None se não estiver presente
    admin_id_alderon = data.get('AdminAlderonId')
    role = data.get('Role')  # None se não estiver presente

    # Construir o comando de inserção com valores opcionais
    insert_admin = admin_command_table.insert().values(
        server_guid=data['ServerGuid'],
        admin_name=data['AdminName'],
        admin_id_alderon=admin_id_alderon,
        role=role,
        command=data['Command'],
    )
    sql_con.execute_query(insert_admin)
    return "Sucesso", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=7001)
