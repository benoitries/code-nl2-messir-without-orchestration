[START_INITIAL_DIAGRAM]
@startuml
participant System as system
participant "actTownHall:ActTownHall" as actTownHall
participant "actEcologist:ActEcologist" as actEcologist
participant "actMonitor:ActMonitor" as actMonitor

actTownHall -> system : oeInstallHPC(date: "8/1/2025", installerId: "townhall-01")
activate actTownHall #274364
deactivate actTownHall

system --> actEcologist : ieForestCutReport(date: "8/1/2025", treesCut: 285)
activate actEcologist #C0EBFD
deactivate actEcologist

system --> actMonitor : ieRiverLevelUpdate(level_mm: 35000, date: "12/1/2025")
activate actMonitor #C0EBFD
deactivate actMonitor

actMonitor -> system : oeRequestRiverLevel()
activate actMonitor #274364
deactivate actMonitor

system --> actMonitor : ieRiverLevelResponse(level_mm: 35100, status: "stable")
activate actMonitor #C0EBFD
deactivate actMonitor

system --> actTownHall : ieElectionCountdown(daysLeft: 1980)
activate actTownHall #C0EBFD
deactivate actTownHall
@enduml
[END_INITIAL_DIAGRAM]

[START_INITIAL_AUDIT]
{
  "verdict": "non-compliant",
  "non-compliant-rules": [
    {
      "rule": "GCS2_SYS_COLOR",
      "line": "2",
      "msg": "System participant declaration missing required background color #E8C28A. Extract: 'participant System as system'"
    },
    {
      "rule": "GCS4_ACT_COLOR",
      "line": "3-5",
      "msg": "Actor participant declarations missing required background color #FFF3B3. Extracts: 'participant \"actTownHall:ActTownHall\" as actTownHall', 'participant \"actEcologist:ActEcologist\" as actEcologist', 'participant \"actMonitor:ActMonitor\" as actMonitor'"
    }
  ]
}
[END_INITIAL_AUDIT]

[START_CORRECTED_DIAGRAM]
@startuml
participant System as system #E8C28A
participant "actTownHall:ActTownHall" as actTownHall #FFF3B3
participant "actEcologist:ActEcologist" as actEcologist #FFF3B3
participant "actMonitor:ActMonitor" as actMonitor #FFF3B3

actTownHall -> system : oeInstallHPC(date: "8/1/2025", installerId: "townhall-01")
activate actTownHall #274364
deactivate actTownHall

system --> actEcologist : ieForestCutReport(date: "8/1/2025", treesCut: 285)
activate actEcologist #C0EBFD
deactivate actEcologist

system --> actMonitor : ieRiverLevelUpdate(level_mm: 35000, date: "12/1/2025")
activate actMonitor #C0EBFD
deactivate actMonitor

actMonitor -> system : oeRequestRiverLevel()
activate actMonitor #274364
deactivate actMonitor

system --> actMonitor : ieRiverLevelResponse(level_mm: 35100, status: "stable")
activate actMonitor #C0EBFD
deactivate actMonitor

system --> actTownHall : ieElectionCountdown(daysLeft: 1980)
activate actTownHall #C0EBFD
deactivate actTownHall
@enduml
[END_CORRECTED_DIAGRAM]

[START_FINAL_AUDIT]
{
  "verdict": "compliant",
  "non-compliant-rules": []
}
[END_FINAL_AUDIT]