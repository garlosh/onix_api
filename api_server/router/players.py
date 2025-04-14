from fastapi import APIRouter, HTTPException
from api_server.dependencies import sql_con, path_rcon_client, ancient_stats
from api_server.utils.functions import (
    calcular_tempo_total_jogador,
    regression,
    convert_to_geometry
)
from random import choice
from sqlalchemy.sql import text, select
from api_server.router.data_models.playerModels import *
from pandas import read_sql

router = APIRouter(prefix="/pot")

# Constants
MIN_PLAY_TIME = 6.0  # Minimum play time in hours
MAX_PLAY_TIME = 60.0  # Maximum play time in hours


@router.post('/respawn', response_model=dict[str, str])
async def respawn(data: RespawnData):
    """
    Handle player respawn events and ancient dinosaur mechanics.

    This endpoint:
    1. Closes any open sessions for the player
    2. Records new respawn
    3. Handles ancient dinosaur stats and bonuses
    """
    # Get required database tables
    respawns_table = sql_con.TABLES["respawns"]
    ancioes_table = sql_con.TABLES["ancioes"]
    stats_tiers_dinos = sql_con.TABLES["stats_tiers_dinos"]
    dinos = sql_con.TABLES["dinos"]

    # Close existing sessions and create new respawn
    sql_con.execute_query(
        respawns_table.update()
        .where(
            (respawns_table.c.id_alderon == data.PlayerAlderonId) &
            (respawns_table.c.data_logout.is_(None))
        )
        .values(data_logout=text("NOW()"))
    )

    # Record new respawn
    sql_con.execute_query(
        respawns_table.insert().values(
            server_guid=data.ServerGuid,
            id_alderon=data.PlayerAlderonId,
            nome_player=data.PlayerName,
            id_dino=data.CharacterID,
            nome_dino=data.CharacterName
        )
    )

    # Calculate total play time in hours
    time_played = calcular_tempo_total_jogador(
        sql_con, data.PlayerAlderonId, data.CharacterID) / 3600

    # Check for existing ancient status
    with sql_con.ENGINE.connect() as connection:
        normal_ancient = connection.execute(
            ancioes_table.select().where(
                (ancioes_table.c.id_alderon == data.PlayerAlderonId) &
                (ancioes_table.c.id_dino == data.CharacterID) &
                (ancioes_table.c.tipo_anciao == 'normal')
            )
        ).fetchone()

    # Get dinosaur stats information
    verifica_stats = select(dinos, stats_tiers_dinos).select_from(
        dinos.outerjoin(
            stats_tiers_dinos,
            dinos.c.tier == stats_tiers_dinos.c.tier
        )
    )
    result = read_sql(verifica_stats, sql_con.ENGINE)
    dino_stats = result[result['nome_over'] == data.DinosaurType]

    if dino_stats.empty:
        raise HTTPException(
            status_code=500,
            detail="Failed to find dinosaur in database"
        )

    # Handle ancient dinosaur logic
    stat_increases = {}

    if normal_ancient:
        # Process existing ancient
        stat1, stat2 = normal_ancient.stat1, normal_ancient.stat2

        # Assign second stat if missing
        if stat2 is None:
            stat2 = choice(ancient_stats)
            with sql_con.ENGINE.connect() as connection:
                connection.execute(
                    ancioes_table.update()
                    .where(
                        (ancioes_table.c.id_alderon == data.PlayerAlderonId) &
                        (ancioes_table.c.nome_dino == data.CharacterName)
                    )
                    .values(stat2=stat2)
                )
                connection.commit()

        # Calculate stat increases
        for stat in [stat1, stat2]:
            increase = regression(
                MIN_PLAY_TIME,
                float(dino_stats[f'{stat}_min'].iloc[0]),
                MAX_PLAY_TIME,
                float(dino_stats[f'{stat}_max'].iloc[0]),
                time_played
            )
            stat_increases[stat] = stat_increases.get(stat, 0) + increase

    # Process new ancient dinosaur
    elif data.DinosaurGrowth == 1.0 and time_played > MIN_PLAY_TIME:
        stat1, stat2 = choice(ancient_stats), choice(ancient_stats)

        # Calculate stats for new ancient
        for stat in [stat1, stat2]:
            increase = regression(
                MIN_PLAY_TIME,
                float(dino_stats[f'{stat}_min'].iloc[0]),
                MAX_PLAY_TIME,
                float(dino_stats[f'{stat}_max'].iloc[0]),
                time_played
            )
            stat_increases[stat] = stat_increases.get(stat, 0) + increase

        # Record new ancient
        with sql_con.ENGINE.connect() as connection:
            connection.execute(
                ancioes_table.insert().values(
                    id_alderon=data.PlayerAlderonId,
                    nome_player=data.PlayerName,
                    id_dino=data.CharacterID,
                    nome_dino=data.CharacterName,
                    stat1=stat1,
                    stat2=stat2,
                    tipo_anciao='normal'
                )
            )
            connection.commit()
    else:
        return {"message": "Success"}

    # Apply stat increases and notify players
    for stat, increase in stat_increases.items():
        path_rcon_client.execute_rcommand(
            f"modattr {data.PlayerAlderonId} {stat} {round(increase, 4)}"
        )
        path_rcon_client.execute_rcommand(
            f"whisper {data.PlayerAlderonId} você recebeu o stat {stat} em decorrência do seu Ancião!"
        )

    path_rcon_client.execute_rcommand(
        "systemmessageall Um dinosauro ancião conectou no servidor!"
    )

    return {"message": "Success"}


@router.post('/leave', response_model=dict[str, str])
async def leave(data: LeaveData):
    """
    Registra quando um jogador sai do servidor.
    """
    if data.FromDeath:
        return {"message": "Success"}

    respawns_table = sql_con.TABLES["respawns"]

    try:
        # Fecha todas as sessões abertas para este jogador/personagem
        close_sessions = (
            respawns_table.update()
            .where(
                (respawns_table.c.id_alderon == data.PlayerAlderonId) &
                (respawns_table.c.nome_dino == data.CharacterName) &
                (respawns_table.c.data_logout.is_(None))
            )
            .values(data_logout=text("NOW()"))
        )

        result = sql_con.execute_query(close_sessions)

        if result.rowcount == 0:
            # Se nenhuma sessão aberta foi encontrada, cria uma retroativa
            insert_respawn = respawns_table.insert().values(
                server_guid=data.ServerGuid,
                id_alderon=data.PlayerAlderonId,
                nome_player=data.PlayerName,
                nome_dino=data.CharacterName,
                data_login=text("DATE_SUB(NOW(), INTERVAL 1 MINUTE)"),
                data_logout=text("NOW()")
            )
            sql_con.execute_query(insert_respawn)
            return {"message": "Created and closed retroactive session"}

        return {"message": f"Closed {result.rowcount} open sessions"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process leave request: {str(e)}"
        )


@router.post('/killed', response_model=dict[str, str])
async def killed(data: KilledData):
    """
    Registra a morte de um jogador no servidor.

    Args:
        VictimCharacterName: Nome do personagem da vítima
        VictimAlderonId: ID Alderon da vítima
        VictimName: Nome do jogador vítima
        VictimDinosaurType: Tipo do dinossauro da vítima
        KillerAlderonId: ID Alderon do assassino
        KillerName: Nome do jogador assassino
        KillerCharacterName: Nome do personagem do assassino
        KillerDinosaurType: Tipo do dinossauro do assassino
        DamageType: Tipo de dano que causou a morte
    """
    ancioes_table = sql_con.TABLES["ancioes"]
    respawns_table = sql_con.TABLES["respawns"]
    log_mortes_table = sql_con.TABLES["log_mortes"]

    # Insert death log
    insert_morte = log_mortes_table.insert().values(
        victim_id=data.VictimAlderonId,
        victim_name=data.VictimName,
        victim_char_name=data.VictimCharacterName,
        victim_dino=data.VictimDinosaurType,
        killer_id=data.KillerAlderonId,
        killer_name=data.KillerName,
        damage_type=data.DamageType,
        killer_char_name=data.KillerCharacterName,
        killer_dino=data.KillerDinosaurType
    )
    sql_con.execute_query(insert_morte)

    # Remover ancião normal
    delete_anciao = ancioes_table.delete().where(
        (ancioes_table.c.id_alderon == data.VictimAlderonId) &
        (ancioes_table.c.nome_dino == data.VictimCharacterName) &
        (ancioes_table.c.tipo_anciao == 'normal')
    )
    sql_con.execute_query(delete_anciao)

    # Remover respawn correspondente
    delete_respawn = respawns_table.delete().where(
        (respawns_table.c.id_alderon == data.VictimAlderonId) &
        (respawns_table.c.nome_dino == data.VictimCharacterName)
    )
    sql_con.execute_query(delete_respawn)

    return {"message": "Success"}


@router.post('/login', response_model=dict[str, str])
async def login(data: LoginData):
    """
    Registra o login de um jogador no servidor.

    Args:
        ServerGuid: ID do servidor
        ServerName: Nome do servidor
        PlayerName: Nome do jogador
        AlderonId: ID Alderon do jogador
        BattlEyeGUID: GUID do BattlEye
        bServerAdmin: Se o jogador é admin do servidor
    """
    jogadores_table = sql_con.TABLES["jogadores"]

    # Inserir ou ignorar dados do jogador
    insert_jogador = jogadores_table.insert().prefix_with('IGNORE').values(
        id_alderon=data.AlderonId,
        server_guid=data.ServerGuid,
        server_name=data.ServerName,
        player_name=data.PlayerName
    )

    sql_con.execute_query(insert_jogador)

    return {"message": "Success"}


@router.post('/server_start')
async def server_start():
    # Comando RCON para iniciar o modo de criador
    path_rcon_client.execute_rcommand("loadcreatormode 1")

    return {"message": "Sucesso"}


@router.post('/server_error', response_model=dict[str, str])
async def server_error(data: ServerErrorData):
    """
    Registra erros do servidor.

    Args:
        ServerGuid: ID do servidor
        ServerIP: IP do servidor
        ServerName: Nome do servidor
        UUID: ID único universal do servidor
        Provider: Provedor do servidor
        Instance: Instância do servidor
        Session: Sessão do servidor
        ErrorMesssage: Mensagem de erro
    """
    server_error_table = sql_con.TABLES["server_error"]

    insert_error = server_error_table.insert().values(
        server_guid=data.ServerGuid,
        server_ip=data.ServerIP,
        server_name=data.ServerName,
        uuid=data.UUID,
        provider=data.Provider,
        instance=data.Instance,
        session=data.Session,
        error_message=data.ErrorMesssage
    )
    sql_con.execute_query(insert_error)
    return {"message": "Success"}


@router.post('/player_report', response_model=dict[str, str])
async def player_report(data: PlayerReportData):
    """
    Registra um report de jogador no servidor.

    Args:
        ServerGuid: ID do servidor
        ReporterPlayerName: Nome do jogador que reportou
        ReporterAlderonId: ID Alderon do jogador que reportou
        ServerName: Nome do servidor
        Secure: Se o servidor é seguro
        ReportedPlayerName: Nome do jogador reportado
        ReportedAlderonId: ID Alderon do jogador reportado
        ReportedPlatform: Plataforma do jogador reportado
        ReportType: Tipo do report
        ReportReason: Razão do report
        RecentDamageCauserIDs: IDs dos causadores de dano recentes
        NearbyPlayerIDs: IDs dos jogadores próximos
        Title: Título do report
        Message: Mensagem do report
        Location: Localização do incidente
        Version: Versão do jogo
        Platform: Plataforma do reporter
    """
    player_report_table = sql_con.TABLES['player_report']

    insert_report = player_report_table.insert().values(
        server_guid=data.ServerGuid,
        reporter_player_name=data.ReporterPlayerName,
        reporter_player_id=data.ReporterAlderonId,
        server_name=data.ServerName,
        reported_player_name=data.ReportedPlayerName,
        reported_alderon_id=data.ReportedAlderonId,
        reported_platform=data.ReportedPlatform,
        report_type=data.ReportType,
        report_reason=data.ReportReason,
        recent_damage_causer_ids=data.RecentDamageCauserIDs,
        nearby_players_id=data.NearbyPlayerIDs,
        title=data.Title,
        message=data.Message,
        location=convert_to_geometry(data.Location),
        platform=data.Platform
    )
    sql_con.execute_query(insert_report)

    return {"message": "Success"}


@router.post('/bad_average_tick', response_model=dict[str, str])
async def bad_average_tick(data: BadAverageTickData):
    """
    Registra informações sobre tick rate baixo no servidor.

    Args:
        ServerGuid: ID do servidor
        ServerIP: IP do servidor
        ServerName: Nome do servidor
        UUID: ID único universal do servidor
        Provider: Provedor do servidor
        Instance: Instância do servidor
        Session: Sessão do servidor
        AverageTickRate: Taxa média de tick
        CurrentTickRate: Taxa atual de tick
        PlayerCount: Número de jogadores
    """
    bad_average_tick_table = sql_con.TABLES['bad_average_tick']

    insert_tick = bad_average_tick_table.insert().values(
        server_guid=data.ServerGuid,
        server_ip=data.ServerIP,
        server_name=data.ServerName,
        uuid=data.UUID,
        provider=data.Provider,
        instance=data.Instance,
        session=data.Session,
        average_tick_rate=data.AverageTickRate,
        current_tick_rate=data.CurrentTickRate,
        player_count=data.PlayerCount
    )
    sql_con.execute_query(insert_tick)
    return {"message": "Success"}


@router.post('/admin_command', response_model=dict[str, str])
async def admin_command(data: AdminCommandData):
    """
    Registra comandos de administrador executados no servidor.

    Args:
        ServerGuid: ID do servidor
        AdminName: Nome do administrador
        AdminAlderonId: ID Alderon do administrador (opcional)
        Role: Cargo do administrador (opcional)
        Command: Comando executado
    """
    admin_command_table = sql_con.TABLES['admin_commands']

    insert_admin = admin_command_table.insert().values(
        server_guid=data.ServerGuid,
        admin_name=data.AdminName,
        admin_id_alderon=data.AdminAlderonId,
        role=data.Role,
        command=data.Command
    )
    sql_con.execute_query(insert_admin)
    return {"message": "Success"}


@router.post('/spectate', response_model=dict[str, str])
async def spectate(data: SpectateData):
    """
    Registra quando um administrador entra ou sai do modo espectador.

    Args:
        ServerGuid: ID do servidor
        AdminName: Nome do administrador
        AdminAlderonId: ID Alderon do administrador
        Action: Ação realizada no modo espectador
    """
    # Tabela de respawn
    respawns_table = sql_con.TABLES["respawns"]

    # Subconsulta para obter o registro mais recente
    subquery = select(respawns_table.c.id).where(
        (respawns_table.c.id_alderon == data.AdminAlderonId)
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


@router.post('/logout', response_model=dict[str, str])
async def logout(data: LogoutData):
    """
    Registra quando um jogador sai definitivamente do servidor (logout).

    Args:
        ServerGuid: ID do servidor
        ServerName: Nome do administrador
        PlayerName: ID Alderon do administrador
        AlderonId: Ação realizada no modo espectador
        BattlEyeGUID: GUID do BattlEye
    """
    # Tabela de respawn
    respawns_table = sql_con.TABLES["respawns"]

    # Fecha todas as conexões em aberto do jogador
    subquery = respawns_table.update().where(
        (respawns_table.c.id_alderon == data.AlderonId) &
        (respawns_table.c.data_logout.is_(None))).values(
            data_logout=text("NOW()")
    )

    try:
        sql_con.execute_query(subquery)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/group_join', response_model=dict[str, str])
async def group_join(data: GroupData):
    """
    Registra quando um jogador entra em um grupo.

    Args:
        ServerGuid: ID do servidor
        Player: Nome do jogador 
        PlayerAlderonId: ID Alderon do jogador
        Leader: Nome do líder
        LeaderAlderonId: ID Alderon do líder
        GroupID: ID do grupo
    """
    grupos_table = sql_con.TABLES['grupos']

    # Insere nova entrada no grupo
    insert_grupo = grupos_table.insert().values(
        group_id=data.GroupID,
        player_name=data.Player,
        player_id=data.PlayerAlderonId,
        leader_name=data.Leader,
        leader_id=data.LeaderAlderonId
    )

    try:
        sql_con.execute_query(insert_grupo)
        return {"message": "Success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/group_leave', response_model=dict[str, str])
async def group_leave(data: GroupData):
    """
    Registra quando um jogador sai de um grupo.

    Args:
        ServerGuid: ID do servidor
        Player: Nome do jogador
        PlayerAlderonId: ID Alderon do jogador
        GroupID: ID do grupo
    """
    grupos_table = sql_con.TABLES['grupos']

    # Atualiza a data de saída do jogador no grupo
    update_grupo = (
        grupos_table.update()
        .where(
            (grupos_table.c.player_id == data.PlayerAlderonId) &
            (grupos_table.c.group_id == data.GroupID) &
            (grupos_table.c.data_saida.is_(None))
        )
        .values(data_saida=text("NOW()"))
    )

    try:
        result = sql_con.execute_query(update_grupo)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=404, detail="No active group membership found")
        return {"message": "Success"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=str(e))
