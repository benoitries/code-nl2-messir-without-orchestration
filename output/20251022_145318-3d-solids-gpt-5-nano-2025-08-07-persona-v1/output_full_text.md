[START_INITIAL_DIAGRAM]
@startuml
participant System as system
participant "theUser:ActInterface" as theUser

theUser -> system : oeSetupSphere(shapeSize=60, numTurtles=100)
activate theUser
deactivate theUser

system --> theUser : ieSetupDone("sphere", shapeSize=60, numTurtles=100)
activate theUser
deactivate theUser
@enduml
[END_INITIAL_DIAGRAM]
[START_INITIAL_AUDIT]
{
  "verdict": "compliant",
  "non-compliant-rules": []
}
[END_INITIAL_AUDIT]