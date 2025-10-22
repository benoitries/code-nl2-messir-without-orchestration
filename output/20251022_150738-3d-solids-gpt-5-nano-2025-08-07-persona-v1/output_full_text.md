[START_INITIAL_DIAGRAM]
@startuml
participant System as system
participant "operator:ActOperator" as operator

operator -> system : oeSetShape("sphere")
activate operator #274364
deactivate operator

system --> operator : ieSphereRendered("sphere")
activate operator #C0EBFD
deactivate operator

operator -> system : oeSetShape("cube-filled")
activate operator #274364
deactivate operator

system --> operator : ieCubeRendered("cube-filled")
activate operator #C0EBFD
deactivate operator
@enduml
[END_INITIAL_DIAGRAM]

[START_INITIAL_AUDIT]
{
  "verdict": "compliant",
  "non-compliant-rules": []
}
[END_INITIAL_AUDIT]