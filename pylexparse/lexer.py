import collections

import matcher
import nfa
import regex

Token = collections.namedtuple('Token', ['type_name', 'value'])


class Rule(object):
    """The definition of a single token."""
    def __init__(self, name, regex, emitted=True):
        self.name = name
        self.regex = regex
        self.emitted = emitted


class Lexer(object):
    """A lexer for a list of token rules."""
    def __init__(self, rules):
        self._acceptor_rules = {}
        start, end = nfa.State(), nfa.State()
        for rule in rules:
            fragment = matcher.pattern_to_fragment(regex.parse_regex(rule.regex))
            acceptor = fragment.end
            self._acceptor_rules[acceptor] = rule
            start.add_empty_transition(fragment.start)
            fragment.end.add_empty_transition(end)

        self._nfa = nfa.Nfa(start, self._acceptor_rules.keys())

    def lex(self, input_str):
        """Break an input stream into tokens.

        Yields tokens from the input stream, for each token whose rule specifies
        emitted=True.
        """
        token_start = 0
        while token_start < len(input_str):
            # TODO(jasonpr): Don't keep slicing the string!
            acceptors, length = self._nfa.longest_match(input_str[token_start:])

            # All tokens must have nonzero length.
            assert length > 0
            token_end = token_start + length
            token_text = input_str[token_start:token_end]

            # TODO(jasonpr): Resolve conflicting token types.
            assert len(acceptors) == 1
            acceptor = acceptors.pop()
            token = self._acceptor_rules[acceptor]
            if token.emitted:
                yield Token(self._acceptor_rules[acceptor].name, token_text)
            token_start = token_end
