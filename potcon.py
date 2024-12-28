from flask import Flask, request
from classes import sqlHandler
from classes import pathcon
import re
import time

app = Flask(__name__)
sql_con = sqlHandler.Client('mysql', 'pymysql', 'adm', 'Cabeca0213', '127.0.0.1', '3306', 'projeto_onix', 'logins')
path_rcon_client = pathcon.client('191.255.115.138', 7779, 'Cucetinha')


@app.route('/pot/respawn', methods=['POST'])
def respawn():
    data = request.get_json()
    player_name = data['PlayerName']
    alderon_id = data['PlayerAlderonId']
    dinosaur = data['DinosaurType']
    growth = data['DinosaurGrowth']
    sql_con.execute_query(f'''INSERT INTO logins (id_alderon, nome, nome_dino, type)
                            VALUES ({player_name}, '{alderon_id}', '{dinosaur}', 1);
                            ''')
    
    if growth == 1.0:
        path_rcon_client.execute_rcommand(f'modattr {alderon_id} Stamina 1')
        path_rcon_client.execute_rcommand(f'announce Um dinosauro anci\u00c2o conectou no servidor!')
    
    
@app.route('/pot/leave', methods=['POST'])
def logout():
    data = request.get_json()
    player_name = data['PlayerName']
    alderon_id = data['PlayerAlderonId']
    dinosaur = data['DinosaurType']
    sql_con.execute_query(f'''INSERT INTO logins (id_alderon, nome, nome_dino, type)
                            VALUES ({player_name}, '{alderon_id}', '{dinosaur}', 0);
                            ''')
    
    
@app.route('/pot/kill', method=['POST'])
def kill():
    data = request.get_json()
if __name__ == '__main__':
    # run app in debug mode on port 80
    app.run(debug=True, port=80)