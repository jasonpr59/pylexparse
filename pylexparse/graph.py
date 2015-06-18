"""Graph utilities."""

import collections

def reachable(start_node):
    """Yields each node reachable from a start node exactly once."""
    return dfs(start_node)

def dfs(start_node):
    """Yields each node reachable from a start node exactly once, using DFS."""
    agenda = collections.deque()
    visited = set()

    agenda.append(start_node)

    while agenda:
        node = agenda.pop()
        if node in visited:
            continue
        visited.add(node)
        yield node

        # Add all successors. If they're duplicates, we'll discard
        # them when we pop them.
        agenda.extend(node.successors())
