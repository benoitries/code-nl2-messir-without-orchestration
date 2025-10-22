[START_INITIAL_DIAGRAM]
@startuml
participant System as system
participant "actUser:ActUser" as actUser

actUser -> system : oeSetupSphere("shape=sphere")
activate actUser
deactivate actUser

system --> actUser : ieSphereReady("shape=sphere")
activate actUser
deactivate actUser
@enduml
[END_INITIAL_DIAGRAM]

[START_INITIAL_AUDIT]
{
  "verdict": "compliant",
  "non-compliant-rules": []
}
[END_INITIAL_AUDIT]