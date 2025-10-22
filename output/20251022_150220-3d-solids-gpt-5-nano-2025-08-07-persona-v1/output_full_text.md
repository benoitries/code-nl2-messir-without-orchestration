[START_INITIAL_DIAGRAM]
@startuml
participant System as system
participant "actController:ActSimulatorController" as controller

controller -> system : oeSetupSphere(800,50)
activate controller
deactivate controller

system --> controller : ieSphereReady(800)
activate controller
deactivate controller

controller -> system : oeGo(1)
activate controller
deactivate controller

system --> controller : ieStatusUpdate("running")
activate controller
deactivate controller
@enduml
[END_INITIAL_DIAGRAM]
[START_INITIAL_AUDIT]
{
  "verdict": "compliant",
  "non-compliant-rules": []
}
[END_INITIAL_AUDIT]