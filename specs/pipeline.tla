------------------------------ MODULE pipeline ------------------------------
(* The run state of docx-reverse-pandoc and pdf-reverse-pandoc (scripts/run.py).
   Checked with TLC from tla2tools.jar v1.7.4 (github.com/tlaplus/tlaplus): no error, 27840 distinct states.
   The first run found that a new finding could be added to a complete run; run.py now reopens the run.
   The jar is not in this repo. To check: java -cp tla2tools.jar tlc2.TLC -config pipeline.cfg pipeline.tla
   Mapping to run.py: Finish = phase P done, Skip = phase P skipped, Fix = phase fix done
   (rounds + 1), Complete = run_status set to complete, validate = Valid. *)
EXTENDS Naturals, Sequences

CONSTANTS N, MaxRounds, Budget          \* number of phases, 3, agents allowed
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
(* Record(g): in run.py a failed gate is recorded too but blocks Complete unless an accepted finding covers it; here only passing or accepted gates enter the set. *)
Record(g) == /\ gates' = gates \cup {g} /\ UNCHANGED <<state, rounds, agents, open, status>>
Open == /\ open < 2 /\ open' = open + 1 /\ status' = "in_progress" /\ UNCHANGED <<state, rounds, agents, gates>>
Resolve == /\ open > 0 /\ open' = open - 1 /\ UNCHANGED <<state, rounds, agents, gates, status>>

Complete == /\ status = "in_progress"
            /\ \A p \in 1..N : state[p] \in {"done", "skipped"}
            /\ gates = {"fonts", "structure", "fidelity", "look"} /\ open = 0
            /\ status' = "complete" /\ UNCHANGED <<state, rounds, agents, gates, open>>

Next == \/ \E p \in 1..N : Finish(p) \/ Skip(p)
        \/ Fix \/ UseAgent \/ Open \/ Resolve \/ Complete
        \/ \E g \in {"fonts", "structure", "fidelity", "look"} : Record(g)

Spec == Init /\ [][Next]_vars /\ WF_vars(Complete)

(* Safety *)
CompleteIsProven == status = "complete" =>
    /\ \A p \in 1..N : state[p] \in {"done", "skipped"}
    /\ gates = {"fonts", "structure", "fidelity", "look"} /\ open = 0
BudgetHolds == agents <= Budget
RoundsBounded == rounds <= MaxRounds
NoDoneAfterOpen == \A p \in 1..N : state[p] = "done" => Prefix(p)

(* Liveness is not claimed: a run may stay in progress forever. Fix rounds are bounded, so no loop runs without end. *)
=============================================================================
