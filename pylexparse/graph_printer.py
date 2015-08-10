"""Converts graphs into the DOT representation."""

import cStringIO

import graph as graphutil

class Registrar(object):
    """Assigns sensible IDs to unique, hashable objects."""
    def __init__(self):
        self._next_id = 1
        self._ids = {}

    def get_id(self, obj):
        try:
            return self._ids[obj]
        except KeyError:
            new_id = self._next_id
            self._next_id += 1
            self._ids[obj] = new_id
            return new_id

def as_dot(graph):
    output = cStringIO.StringIO()
    print >>output, 'digraph unnamed{'

    # The registrar provides small, unique numbers as node names.
    registrar = Registrar()

    print >>output, 'invisible_start_source [style="invisible"]'
    print >>output, 'invisible_start_source -> %d[shape="none", style="bold"]' % (
        registrar.get_id(graph.start))

    for node in graphutil.reachable(graph.start):
        print >>output, '%d [shape="%s"]' % (
            registrar.get_id(node),
            'doublecircle' if node in graph.accepting_states else 'circle',
            )
        for edge_name, successor in node:
            print >>output, '%d -> %d [label="%s"]' % (
                registrar.get_id(node),
                registrar.get_id(successor),
                edge_name)

    print >>output, '}'

    result = output.getvalue()
    output.close()

    return result
