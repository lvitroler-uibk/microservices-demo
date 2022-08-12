from GetLogs import mainLogs
from GetTraces import mainTraces
from GetMonitoringData import mainMonitoringData

Authentication = "sha256~BhFivk7wCVvTgXPbw_6v9CwrWz9_YpDfvQr9EHSF-IY"

if __name__ == "__main__":
    print("data is now getting collected")
    called_version = "ts-admin-basic-info-service_springstarterweb_1.5.22.RELEASE"
    #TODO alle Version Updates in einem Ordner zusammensammeln

    mainLogs("LOGS_" + called_version + ".txt")
    mainTraces(called_version)
    mainMonitoringData(called_version + ".json")
    print("Data Collection is finished!")