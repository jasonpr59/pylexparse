import collections
import sets

import dfa
import nfa as nfas


class NfaStateSet(sets.ImmutableSet):
    """An immutable set of NFA states."""

    
def nfa_to_dfa(nfa):

    # Maps NfaStateSet -> dfa.State.
    dfa_states = collections.defaultdict(dfa.State)

    # Discover all dfa_states, worklist-style.
    worklist = collections.deque()
    done = set()
    start_nss = NfaStateSet(nfas.epsilon_closure([nfa.start]))
    worklist.append(start_nss)

    while worklist:
        focus = worklist.pop()
        if focus in done:
            continue
        done.add(focus)
            
        dfa_transitions = collections.defaultdict(set)
        for nfa_state in focus:
            for char, nfa_dest in nfa_state:
                if not char:
                    # Empty transitions are dealt with separately (by finding epsilon closures).
                    continue
                dfa_transitions[char].add(nfa_dest)

        for char, next_states in dfa_transitions.iteritems():
            next_set = NfaStateSet(nfas.epsilon_closure(next_states))
            worklist.append(next_set)
            dfa_states[focus].add_transition(char, dfa_states[next_set])
    
    accepting_states = set(dfa_state for nss, dfa_state in dfa_states.iteritems() if nfa.accepting.intersection(nss))

    return dfa.Dfa(dfa_states[start_nss], accepting_states)
