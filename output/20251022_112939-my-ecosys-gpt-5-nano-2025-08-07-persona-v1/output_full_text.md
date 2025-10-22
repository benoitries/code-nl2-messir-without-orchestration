[START_INITIAL_DIAGRAM]
@startuml
participant System as system
participant "actOperator:ActOperator" as actOperator

actOperator -> system : oeInstallHPC("config=default")
activate actOperator
deactivate actOperator

system --> actOperator : ieHPCInstallStatus("OK")
activate actOperator
deactivate actOperator
@enduml
[END_INITIAL_DIAGRAM]

[START_INITIAL_AUDIT]
{
  "verdict": "non-compliant",
  "non-compliant-rules": [
    {
      "rule": "AS2_SYS_DECLARED_FIRST",
      "line": "1",
      "msg": "System must be declared first before all actors."
    }
    ]
}
[END_INITIAL_AUDIT]

[START_CORRECTED_DIAGRAM]
@startuml
participant System as system
participant "actOperator:ActOperator" as actOperator

actOperator -> system : oeInstallHPC("config=default")
activate actOperator
deactivate actOperator

system --> actOperator : ieHPCInstallStatus("OK")
activate actOperator
deactivate actOperator
@enduml
[END_CORRECTED_DIAGRAM]

[START_FINAL_AUDIT]
{
  "verdict": "compliant",
  "non-compliant-rules": []
}
[END_FINAL_AUDIT]