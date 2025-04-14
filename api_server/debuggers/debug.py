import sys
import os
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

from common.sqlHandler import Client
from common.pathcon import client
from sqlalchemy.sql import text, select
import json
from pdb import set_trace
from pandas import read_sql
sql_con = Client(
    'mysql', 'pymysql', 'adm', 'cabeca0213', '192.168.0.134', '3306', 'projeto_onix')
path_rcon_client = client('192.168.0.134', 7779, 'Cucetinha')


# Carregar configurações
with open('config.json') as json_file:
    ancient_stats = json.load(json_file)

# Inicializar tabelas
tables = ["respawns", "ancioes", "server_error",
          "jogadores", "player_report", "admin_commands", "log_mortes", "grupos", "stats_tiers_dinos", "dinos"]
for table in tables:
    sql_con.get_table_metadata(table)

if __name__ == '__main__':
    ancioes_table = sql_con.TABLES["ancioes"]
    # Obtendo as referências das tabelas
    # Consultar ancião normal
    normal_ancient_query = ancioes_table.select().where(
        (ancioes_table.c.id_alderon == "028-686-803") &
        (ancioes_table.c.id_dino == "BDBF419A71D5406885782E7AC317C727") &
        (ancioes_table.c.tipo_anciao == 'normal')
    )
    with sql_con.ENGINE.connect() as connection:
        normal_ancient = connection.execute(normal_ancient_query).fetchone()
    set_trace()  # Para debugar e ver o resultado
