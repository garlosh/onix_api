from dataclasses import dataclass
from sqlalchemy import create_engine, text, Table, MetaData, insert
import pandas as pd


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
        self.METADATA = MetaData(bind=self.ENGINE)

    def execute_query(self, query) -> None:
        with self.ENGINE.connect() as connection:
            connection.execute(text(query))
            connection.commit()

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

    def insert_json(self, table_name: str, json_data: dict) -> None:
        """
        Insere um JSON em uma tabela existente no banco de dados.

        Args:
            table_name (str): Nome da tabela no banco de dados.
            json_data (dict): Dicionário contendo os dados a serem inseridos.
        """
        try:
            # Refletir a tabela existente
            table = Table(table_name, self.METADATA, autoload_with=self.ENGINE)

            # Criar instrução de inserção
            stmt = insert(table).values(json_data)

            # Executar a instrução
            with self.ENGINE.connect() as connection:
                connection.execute(stmt)
                connection.commit()

            print(f"JSON inserido com sucesso na tabela '{table_name}'.")
        except Exception as e:
            print(f"Erro ao inserir JSON na tabela '{table_name}': {e}")
