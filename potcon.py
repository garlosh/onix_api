from flask import Flask, request
from classes import sqlHandler
from classes import pathcon
from utils import *
from random import choice
from gevent.pywsgi import WSGIServer
import json
app = Flask(__name__)
sql_con = sqlHandler.Client('mysql', 'pymysql', 'adm',
                            'cabeca0213', '127.0.0.1', '3306', 'projeto_onix')
path_rcon_client = pathcon.client('127.0.0.1', 7779, 'Cucetinha')

with open('config.json') as json_file:
    ancient_stats = json.load(json_file)


@app.route('/pot/respawn', methods=['POST'])
def respawn():
    min_time, max_time = 15.0, 45.0

    data = request.get_json()
    player_name = data['PlayerName']
    alderon_id = data['PlayerAlderonId']
    dinosaur = data['CharacterName']
    dinosaur_id = data['CharacterID']
    growth = data['DinosaurGrowth']
    server_guid = data['ServerGuid']

    sql_con.execute_query(
        f"""INSERT INTO respawns (server_guid, id_alderon, nome_player, id_dino, nome_dino) \
        VALUES ('{server_guid}', '{alderon_id}', '{player_name}', '{dinosaur_id}', '{dinosaur}');"""
    )

    time_played = calcular_tempo_total_jogador(
        sql_con, alderon_id, dinosaur_id) / 3600

    normal_ancient = sql_con.query_database(
        f"""SELECT * FROM ancioes WHERE id_alderon = '{alderon_id}' AND id_dino = '{
            dinosaur_id}' AND tipo_anciao = 'normal';"""
    )

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
        sql_con.execute_query(
            f"""INSERT INTO ancioes (id_alderon, nome_player, id_dino, nome_dino, stat1, tipo_anciao) \
            VALUES ('{alderon_id}', '{player_name}', '{dinosaur_id}', '{dinosaur}', '{stat}', 'normal');"""
        )
        path_rcon_client.execute_rcommand(
            f"""modattr {alderon_id} {stat} {min_attr}""")
        path_rcon_client.execute_rcommand(
            "systemmessageall Um dinosauro ancião conectou no servidor!")

    special_ancient = sql_con.query_database(
        f"""SELECT * FROM ancioes WHERE id_alderon = '{
            alderon_id}' AND tipo_anciao = 'especial';"""
    )

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
    sql_con.execute_query(f'''
                        UPDATE respawns
                        SET data_logout = NOW()
                        WHERE id_alderon = '{alderon_id}';
                        ''')

    return 'Success', 200


@app.route('/pot/killed', methods=['POST'])
def killed():
    data = request.get_json()
    victim = data['VictimCharacterName']
    alderon_id = data['VictimAlderonId']
    nome_player = data['VictimName']
    sql_con.execute_query(f'''
                        DELETE FROM ancioes
                        WHERE id_alderon = '{alderon_id}' AND nome_player = '{nome_player}' AND nome_dino = '{victim}' AND tipo_anciao = 'normal';
                        ''')
    sql_con.execute_query(f'''
                        DELETE FROM respawns
                        WHERE id_alderon = '{alderon_id}' AND nome_player = '{nome_player}' AND nome_dino = '{victim}';
                        ''')
    return 'Success', 200


@app.route('/pot/server_error', methods=['POST'])
def server_error():
    data = request.get_json()
    sql_con.execute_query(
        f"""INSERT INTO ancioes (server_guid, server_ip, server_name, uuid, provider, instance, session, error_message)
            VALUES ('{data["ServerGuid"]}', '{data["ServerIP"]}', '{data["ServerName"]}', '{data["UUID"]}', '{data["Provider"]}', '{data["Instance"]}', '{data["Session"]}', '{data["ErrorMesssage"]}');"""
    )
    sql_con.insert_json(table_name="server_error", json_data=mapped_data)


@app.route('/pot/player_report', methods=['POST'])
def player_report():
    data = request.get_json()
    mapped_data = {
        "server_guid": data["ServerGuid"],
        "reporter_player_name": data["ReporterPlayerName"],
        "reporter_player_id": data["ReporterAlderonId"],
        "server_name": data["ServerName"],
        "reporeted_player_name": data["ReportedPlayerName"],
        "reported_alderon_id": data["ReportedAlderonId"],
        "reported_platform": data["ReportedPlatform"],
        "report_reason": data["ReportReason"],
        "recent_damage_causer_ids": data["RecentDamageCauserIDs"],
        "nearby_players_id": data["NearbyPlayerIDs"],
        "title": data["Title"],
        "message": data["Message"],
        "location": convert_to_geometry(data["Location"]),
        "platform": data["Platform"],
    }
    sql_con.insert_json(table_name="player_report", json_data=mapped_data)


@app.route('/pot/server_start', methods=['POST'])
def server_start():
    path_rcon_client.execute_rcommand("loadcreatormode 1")
    return "Sucesso", 200


if __name__ == '__main__':
    # run app in debug mode on port 80
    # app_server = WSGIServer(("127.0.0.1", 80), app)
    # app_server.serve_forever()
    app.run(debug=True, port=80)
