from dataclasses import dataclass
from sqlalchemy import create_engine, text, Table, MetaData, insert
from sqlalchemy.sql import Insert, Update, Delete, Select
from sqlalchemy.sql.expression import TextClause
import pandas as pd
from typing import Dict


@dataclass
class Client:
    DB_TYPE: str  # ou 'postgresql', 'sqlite', etc.
    DB_DRIVER: str  # driver apropriado para o seu banco de dados
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: str  # porta apropriada para o seu banco de dados
    DB_NAME: str

    def __post_init__(self) -> None:
        DATABASE_URI = f'{self.DB_TYPE}+{self.DB_DRIVER}://{self.DB_USER}:{
            self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
        self.ENGINE = create_engine(DATABASE_URI)
        self.METADATA: Dict[str, MetaData] = {}
        self.TABLES: Dict[str, Table] = {}

    def get_table_metadata(self, table_name: str) -> None:
        self.METADATA[table_name] = MetaData()
        self.TABLES[table_name] = Table(
            table_name, self.METADATA[table_name], autoload_with=self.ENGINE)

    def execute_query(self, query):
        """
        Executa uma consulta SQLAlchemy ou uma string de consulta SQL.
        """
        with self.ENGINE.connect() as connection:
            # Verifica se é uma string ou cláusula textual
            if isinstance(query, (str, TextClause)):
                result = connection.execute(text(query))
            # Verifica se é uma operação de escrita (Insert, Update, Delete)
            elif isinstance(query, (Insert, Update, Delete)):
                result = connection.execute(query)
                connection.commit()  # Confirma operações de escrita
            # Verifica se é uma consulta Select
            elif isinstance(query, Select):
                # Retorna resultados diretamente
                result = connection.execute(query)
            else:
                raise ValueError(
                    f"Tipo de consulta não suportado: {type(query)}")
            return result

    def query_database(self, query) -> pd.DataFrame:
        resultado = pd.read_sql(query, con=self.ENGINE)
        self.ENGINE.dispose()
        return resultado

    def verify_engine(self) -> bool:
        try:
            self.ENGINE.connect()
            self.ENGINE.dispose()
            return True
        except:
            return False


if __name__ == "__main__":
    sql_con = Client('mysql', 'pymysql', 'adm',
                     'cabeca0213', '192.168.0.134', '3306', 'projeto_onix')
    sql_con.get_table_metadata("respawns")
    print(sql_con.TABLES['respawns'].select())
