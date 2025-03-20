from pydantic import BaseModel


class KilledData(BaseModel):
    ServerGuid: str
    TimeOfDay: int
    DamageType: str
    VictimPOI: str
    VictimName: str
    VictimAlderonId: str
    VictimCharacterName: str
    VictimDinosaurType: str
    VictimRole: str
    VictimIsAdmin: bool
    VictimGrowth: float
    VictimLocation: str
    KillerName: str
    KillerAlderonId: str
    KillerCharacterName: str
    KillerDinosaurType: str
    KillerRole: str
    KillerIsAdmin: bool
    KillerGrowth: float
    KillerLocation: str

    class Config:
        json_schema_extra = {
            "example": {
                "ServerGuid": "63a86971-0cb9-4569-a43a-4b05317f2d73",
                "TimeOfDay": 1300,
                "DamageType": "DT_ATTACK",
                "VictimPOI": "Talons Point",
                "VictimName": "Test1",
                "VictimAlderonId": "048-236-424",
                "VictimCharacterName": "DiloIsCool",
                "VictimDinosaurType": "Dilophosaurus",
                "VictimRole": "CoolRole",
                "VictimIsAdmin": False,
                "VictimGrowth": 0.5,
                "VictimLocation": "(X=328866.125,Y=-130023.359375,Z=853.25)",
                "KillerName": "Test2",
                "KillerAlderonId": "123-430-121",
                "KillerCharacterName": "DiloIsCooler",
                "KillerDinosaurType": "Dilophosaurus",
                "KillerRole": "NotAsCoolRole",
                "KillerIsAdmin": False,
                "KillerGrowth": 0.5,
                "KillerLocation": "(X=328866.125,Y=-130023.359375,Z=853.25)"
            }
        }


class PlayerReportData(BaseModel):
    ServerGuid: str
    ReporterPlayerName: str
    ReporterAlderonId: str
    ServerName: str
    Secure: bool
    ReportedPlayerName: str
    ReportedAlderonId: str
    ReportedPlatform: str
    ReportType: str
    ReportReason: str
    RecentDamageCauserIDs: str
    NearbyPlayerIDs: str
    Title: str
    Message: str
    Location: str
    Version: str
    Platform: str

    class Config:
        json_schema_extra = {
            "example": {
                "ServerGuid": "63a86971-0cb9-4569-a43a-4b05317f2d73",
                "ReporterPlayerName": "Test1",
                "ReporterAlderonId": "048-236-424",
                "ServerName": "Server",
                "Secure": True,
                "ReportedPlayerName": "Test2",
                "ReportedAlderonId": "123-430-121",
                "ReportedPlatform": "Desktop",
                "ReportType": "Killed By User",
                "ReportReason": "KOS (Killed on Sight)",
                "RecentDamageCauserIDs": "123-430-121, 135-654-234",
                "NearbyPlayerIDs": "123-430-121, 135-654-234",
                "Title": "I got killed",
                "Message": "please help!",
                "Location": "(X=328866.125,Y=-130023.359375,Z=853.25)",
                "Version": "0.0.0.12968",
                "Platform": "Desktop"
            }
        }


class LoginData(BaseModel):
    ServerGuid: str
    ServerName: str
    PlayerName: str
    AlderonId: str
    BattlEyeGUID: str
    bServerAdmin: bool

    class Config:
        json_schema_extra = {
            "example": {
                "ServerGuid": "63a86971-0cb9-4569-a43a-4b05317f2d73",
                "ServerName": "Server",
                "PlayerName": "Test1",
                "AlderonId": "048-236-424",
                "BattlEyeGUID": "05db16f3014acfdd6cc48dc7ce99168e",
                "bServerAdmin": False
            }
        }


class BadAverageTickData(BaseModel):
    ServerGuid: str
    ServerIP: str
    ServerName: str
    UUID: str
    Provider: str
    Instance: str
    Session: str
    AverageTickRate: float
    CurrentTickRate: float
    PlayerCount: int

    class Config:
        json_schema_extra = {
            "example": {
                "ServerGuid": "63a86971-0cb9-4569-a43a-4b05317f2d73",
                "ServerIP": "12.32.421.12:7777",
                "ServerName": "Server",
                "UUID": "63a86971-0cb9-4569-a43a-4b05317f2d73",
                "Provider": "AWS",
                "Instance": "i-0b9e7b3b4b7b3b7b3",
                "Session": "12aecb",
                "AverageTickRate": 50.0,
                "CurrentTickRate": 30.0,
                "PlayerCount": 10
            }
        }


class SpectateData(BaseModel):
    ServerGuid: str
    AdminName: str
    AdminAlderonId: str
    Action: str

    class Config:
        json_schema_extra = {
            "example": {
                "ServerGuid": "63a86971-0cb9-4569-a43a-4b05317f2d73",
                "AdminName": "Test1",
                "AdminAlderonId": "048-236-424",
                "Action": "Entered Spectator Mode"
            }
        }


class AdminCommandData(BaseModel):
    ServerGuid: str
    AdminName: str
    AdminAlderonId: str | None = None
    Role: str | None = None
    Command: str

    class Config:
        json_schema_extra = {
            "example": {
                "ServerGuid": "63a86971-0cb9-4569-a43a-4b05317f2d73",
                "AdminName": "Test1",
                "AdminAlderonId": "048-236-424",
                "Role": "Admin",
                "Command": "listplayers"
            }
        }


class ServerErrorData(BaseModel):
    ServerGuid: str
    ServerIP: str
    ServerName: str
    UUID: str
    Provider: str
    Instance: str
    Session: str
    ErrorMesssage: str

    class Config:
        json_schema_extra = {
            "example": {
                "ServerGuid": "63a86971-0cb9-4569-a43a-4b05317f2d73",
                "ServerIP": "12.32.421.12:7777",
                "ServerName": "Server",
                "UUID": "63a86971-0cb9-4569-a43a-4b05317f2d73",
                "Provider": "AWS",
                "Instance": "i-0b9e7b3b4b7b3b7b3",
                "Session": "12aecb",
                "ErrorMesssage": "Error message here"
            }
        }


class LeaveData(BaseModel):
    ServerGuid: str
    PlayerName: str
    PlayerAlderonId: str
    FromDeath: bool
    SafeLog: bool
    CharacterName: str
    DinosaurType: str
    DinosaurGrowth: float
    Location: str

    class Config:
        json_schema_extra = {
            "example": {
                "ServerGuid": "63a86971-0cb9-4569-a43a-4b05317f2d73",
                "PlayerName": "Test1",
                "PlayerAlderonId": "048-236-424",
                "FromDeath": False,
                "SafeLog": True,
                "CharacterName": "DiloIsCool",
                "DinosaurType": "Dilophosaurus",
                "DinosaurGrowth": 0.5,
                "Location": "(X=328866.125,Y=-130023.359375,Z=853.25)"
            }
        }


class RespawnData(BaseModel):
    ServerGuid: str
    PlayerName: str
    PlayerAlderonId: str
    Role: str
    CharacterID: str
    CharacterName: str
    DinosaurType: str
    DinosaurGrowth: float
    Location: str

    class Config:
        json_schema_extra = {
            "example": {
                "ServerGuid": "63a86971-0cb9-4569-a43a-4b05317f2d73",
                "PlayerName": "Test1",
                "PlayerAlderonId": "048-236-424",
                "Role": "CoolRole",
                "CharacterID": "afec432da",
                "CharacterName": "DiloIsCool",
                "DinosaurType": "Dilophosaurus",
                "DinosaurGrowth": 0.5,
                "Location": "(X=328866.125,Y=-130023.359375,Z=853.25)"
            }
        }


class GroupData(BaseModel):
    ServerGuid: str
    Player: str
    PlayerAlderonId: str
    Leader: str
    LeaderAlderonId: str
    GroupID: int

    class Config:
        json_schema_extra = {
            "example": {
                "ServerGuid": "63a86971-0cb9-4569-a43a-4b05317f2d73",
                "Player": "Test1",
                "PlayerAlderonId": "048-236-424",
                "Leader": "Test2",
                "LeaderAlderonId": "123-430-121",
                "GroupID": "3431"
            }
        }
