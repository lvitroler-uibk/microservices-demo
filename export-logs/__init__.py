from GetLogs import mainLogs
from GetTraces import mainTraces
from GetMonitoringData import mainMonitoringData

if __name__ == "__main__":
    print("data is now getting collected")
    called_version = "nofaults"
    #TODO alle Version Updates in einem Ordner zusammensammeln

    mainLogs(called_version)
    mainTraces(called_version)
    mainMonitoringData(called_version + ".json")
    print("Data Collection is finished!")