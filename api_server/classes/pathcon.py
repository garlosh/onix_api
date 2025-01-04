from dataclasses import dataclass
from rcon.source import Client
from typing import Optional
@dataclass
class client:
    IP: str
    PORT: int
    PASS: str
    def execute_rcommand(self, command: str) -> Optional['str']:
        with Client(self.IP, self.PORT, passwd=self.PASS) as client:
            response = client.run(command)
            
        return response
    
if __name__ == '__main__':
    from rcon.source import Client

    with Client('191.255.115.138', 7779, passwd='Cucetinha') as client:
        response = client.run('PlayerInfo 171-232-336')

    print(response)