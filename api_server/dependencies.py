from common.sqlHandler import Client
from common.pathcon import client
import json

# Configuração do SQLHandler e RCON
sql_con = Client(
    'mysql', 'pymysql', 'adm', 'cabeca0213', '127.0.0.1', '3306', 'projeto_onix')
path_rcon_client = client('127.0.0.1', 7779, 'Cucetinha')

# Carregar configurações
# with open('config.json') as json_file:
#    ancient_stats = json.load(json_file)

# Inicializar tabelas
tables = ["respawns", "ancioes", "server_error",
          "jogadores", "player_report", "admin_commands", "log_mortes",
          "grupos", "stats_tiers_dinos", "dinos"]

# Stats de dino
ancient_stats: set = set(["CombatWeight",
                         "CombatWeight",
                          "DamageMultiplier",
                          "DamageMultiplier",
                          "Armor",
                          "MaxStamina",
                          "MaxHealth",
                          "BleedingHealRate",
                          "HealthRecoveryRate"
                          "TurnRadiusMultiplier",
                          "TurnInplaceRadiusMultiplier",
                          "TrottingSpeedMultiplier",
                          "SprintingSpeedMultiplier"])


for table in tables:
    sql_con.get_table_metadata(table)
