------------------------------ MODULE pipeline ------------------------------
(* To check: java -cp tla2tools.jar tlc2.TLC -config pipeline.cfg pipeline.tla *)
EXTENDS Naturals, Sequences

CONSTANTS N, MaxRounds, Budget
VARIABLES state, rounds, agents, gates, open, status
vars == <<state, rounds, agents, gates, open, status>>

PhaseState == {"pending", "done", "skipped"}

Init == /\ state = [p \in 1..N |-> "pending"]
        /\ rounds = 0 /\ agents = 0 /\ gates = {} /\ open = 0 /\ status = "in_progress"

Prefix(p) == \A q \in 1..(p-1) : state[q] \in {"done", "skipped"}

Finish(p) == /\ status = "in_progress" /\ state[p] = "pending" /\ Prefix(p)
             /\ state' = [state EXCEPT ![p] = "done"] /\ UNCHANGED <<rounds, agents, gates, open, status>>

Skip(p) == /\ status = "in_progress" /\ state[p] = "pending"
           /\ state' = [state EXCEPT ![p] = "skipped"] /\ UNCHANGED <<rounds, agents, gates, open, status>>

Fix == /\ status = "in_progress" /\ rounds < MaxRounds
       /\ rounds' = rounds + 1 /\ UNCHANGED <<state, agents, gates, open, status>>

UseAgent == /\ agents < Budget /\ agents' = agents + 1 /\ UNCHANGED <<state, rounds, gates, open, status>>
RecordPassingOrAccepted(g) == /\ gates' = gates \cup {g} /\ UNCHANGED <<state, rounds, agents, open, status>>
Open == /\ open < 2 /\ open' = open + 1 /\ status' = "in_progress" /\ UNCHANGED <<state, rounds, agents, gates>>
Resolve == /\ open > 0 /\ open' = open - 1 /\ UNCHANGED <<state, rounds, agents, gates, status>>

Complete == /\ status = "in_progress"
            /\ \A p \in 1..N : state[p] \in {"done", "skipped"}
            /\ gates = {"fonts", "structure", "fidelity", "look"} /\ open = 0
            /\ status' = "complete" /\ UNCHANGED <<state, rounds, agents, gates, open>>

Next == \/ \E p \in 1..N : Finish(p) \/ Skip(p)
        \/ Fix \/ UseAgent \/ Open \/ Resolve \/ Complete
        \/ \E g \in {"fonts", "structure", "fidelity", "look"} : RecordPassingOrAccepted(g)

Spec == Init /\ [][Next]_vars /\ WF_vars(Complete)

CompleteIsProven == status = "complete" =>
    /\ \A p \in 1..N : state[p] \in {"done", "skipped"}
    /\ gates = {"fonts", "structure", "fidelity", "look"} /\ open = 0
BudgetHolds == agents <= Budget
RoundsBounded == rounds <= MaxRounds
NoDoneAfterOpen == \A p \in 1..N : state[p] = "done" => Prefix(p)

=============================================================================
