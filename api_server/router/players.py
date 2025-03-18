# api/router/players.py
from fastapi import APIRouter, Request, HTTPException
from api_server.dependencies import sql_con, path_rcon_client
from api_server.utils.functions import calcular_tempo_total_jogador, log_regression, convert_to_geometry
from random import choice
from sqlalchemy.sql import text, select
import json

router = APIRouter(prefix="/pot")

# Carregar configurações
with open('config.json') as json_file:
    ancient_stats = json.load(json_file)


@router.post('/respawn')
async def respawn(request: Request):
    min_time, max_time = 6.0, 45.0
    data = await request.json()

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
    with sql_con.ENGINE.connect() as connection:
        normal_ancient = connection.execute(normal_ancient_query).fetchone()
    if normal_ancient:
        stat = normal_ancient.stat1
        min_attr, max_attr = ancient_stats[stat]['min'], ancient_stats[stat]['max']
        stat_increase = log_regression(
            min_time, min_attr, max_time, max_attr, time_played)
        path_rcon_client.execute_rcommand(
            f"modattr {alderon_id} {stat} {round(stat_increase, 2)}")
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
        with sql_con.ENGINE.connect() as connection:
            normal_ancient = connection.execute(insert_anciao)
            connection.commit()
        path_rcon_client.execute_rcommand(
            f"modattr {alderon_id} {stat} {round(min_attr, 2)}")
        path_rcon_client.execute_rcommand(
            "systemmessageall Um dinosauro ancião conectou no servidor!")

    return {"message": "Success"}


@router.post('/pot/leave')
async def leave(request: Request):
    data = await request.json()
    alderon_id = data['PlayerAlderonId']
    nome_dino = data['CharacterName']
    from_death = bool(data['FromDeath'])
    if from_death:
        return {"message": "Success"}, 208
    # Tabela de respawns
    respawns_table = sql_con.TABLES["respawns"]

    # Subconsulta para obter o registro mais recente
    subquery = select(respawns_table.c.id).where(
        (respawns_table.c.id_alderon == alderon_id) &
        (respawns_table.c.nome_dino == nome_dino)
    ).order_by(respawns_table.c.data_login.desc()).limit(1)

    # Executa a subconsulta usando sql_con
    result = sql_con.execute_query(subquery)
    id_to_update = result.scalar() if result else None

    if id_to_update:
        # Atualizar logout do registro mais recente
        update_logout = (
            respawns_table.update()
            .where(respawns_table.c.id == id_to_update)
            .values(data_logout=text("NOW()"))
        )
        sql_con.execute_query(update_logout)
        return {"message": "Success"}
    else:
        raise HTTPException(status_code=404, detail="No matching record found")


@router.post('/killed')
async def killed(request: Request):
    data = await request.json()
    # Extract all required fields from the request
    victim = data['VictimCharacterName']
    alderon_id = data['VictimAlderonId']
    victim_name = data['VictimPlayerName']
    victim_dino = data['VictimDinoType']
    killer_id = data['KillerAlderonId']
    killer_name = data['KillerPlayerName']
    killer_char_name = data['KillerCharacterName']
    killer_dino = data['KillerDinoType']
    damage_type = data['DamageType']

    ancioes_table = sql_con.TABLES["ancioes"]
    respawns_table = sql_con.TABLES["respawns"]
    log_mortes_table = sql_con.TABLES["log_mortes"]

    # Insert death log
    insert_morte = log_mortes_table.insert().values(
        victim_id=alderon_id,
        victim_name=victim_name,
        victim_char_name=victim,
        victim_dino=victim_dino,
        killer_id=killer_id,
        killer_name=killer_name,
        damage_type=damage_type,
        killer_char_name=killer_char_name,
        killer_dino=killer_dino
    )
    sql_con.execute_query(insert_morte)

    # Remover ancião normal
    delete_anciao = ancioes_table.delete().where(
        (ancioes_table.c.id_alderon == alderon_id) &
        (ancioes_table.c.nome_dino == victim) &
        (ancioes_table.c.tipo_anciao == 'normal')
    )
    sql_con.execute_query(delete_anciao)

    # Remover respawn correspondente
    delete_respawn = respawns_table.delete().where(
        (respawns_table.c.id_alderon == alderon_id) &
        (respawns_table.c.nome_dino == victim)
    )
    sql_con.execute_query(delete_respawn)

    return {"message": "Success"}


@router.post('/login')
async def login(request: Request):
    data = await request.json()

    jogadores_table = sql_con.TABLES["jogadores"]

    # Inserir ou ignorar dados do jogador
    insert_jogador = jogadores_table.insert().prefix_with('IGNORE').values(
        id_alderon=data["AlderonId"],
        server_guid=data["ServerGuid"],
        server_name=data["ServerName"],
        player_name=data["PlayerName"]
    )

    sql_con.execute_query(insert_jogador)

    return {"message": "Sucesso"}


@router.post('/server_start')
async def server_start():
    # Comando RCON para iniciar o modo de criador
    path_rcon_client.execute_rcommand("loadcreatormode 1")

    return {"message": "Sucesso"}


@router.post('/server_error')
async def server_error(request: Request):
    data = await request.json()

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
    return {"message": "Sucesso"}


@router.post('/player_report')
async def player_report(request: Request):
    data = await request.json()

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
    return {"message": "Sucesso"}


@router.post('/bad_average_tick')
async def bad_average_tick(request: Request):
    data = await request.json()

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
    return {"message": "Sucesso"}


@router.post('/admin_command')
async def admin_command(request: Request):
    data = await request.json()

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
    return {"message": "Sucesso"}


@router.post('/pot/spectate')
async def spectate(request: Request):
    data = await request.json()
    alderon_id = data['AdminAlderonId']
    # Tabela de respawn
    respawns_table = sql_con.TABLES["respawns"]

    # Subconsulta para obter o registro mais recente
    subquery = select(respawns_table.c.id).where(
        (respawns_table.c.id_alderon == alderon_id)
    ).order_by(respawns_table.c.data_login.desc()).limit(1)

    # Executa a subconsulta usando sql_con
    result = sql_con.execute_query(subquery)
    id_to_update = result.scalar() if result else None

    if id_to_update:
        # Atualizar logout do registro mais recente
        update_logout = (
            respawns_table.update()
            .where(respawns_table.c.id == id_to_update)
            .values(data_logout=text("NOW()"))
        )
        sql_con.execute_query(update_logout)
        return {"message": "Success"}
    else:
        raise HTTPException(status_code=404, detail="No matching record found")
