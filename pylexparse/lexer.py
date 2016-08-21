import collections

import charsource
import nfa
import regex

class Token(collections.namedtuple('Token', ['type_name', 'value'])):
    def __str__(self):
        return '%s(%r)' % (self.type_name, self.value)


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
        self._acceptor_precedences = {}
        start, end = nfa.State(), nfa.State()
        for i, rule in enumerate(rules):
            fragment = regex.parse_regex(rule.regex)._fragment()
            acceptor = fragment.end
            self._acceptor_rules[acceptor] = rule
            # Later rules get higher precedence.  This mimics
            # reassignment in most languages: `x=1; x=2;` means `x==2`.
            self._acceptor_precedences[acceptor] = i
            start.add_empty_transition(fragment.start)
            fragment.end.add_empty_transition(end)

        # Add final EOF transition.
        # The regex for this rule is never used.
        # TODO(jasonpr): Allow a token to exist independently of its regex?
        eof_rule = Rule('EOF', '', emitted=False)
        eof_acceptor = nfa.State()
        # None is our EOF.
        start.add_transition(None, eof_acceptor)
        self._acceptor_rules[eof_acceptor] = eof_rule
        # The EOF's precedence shouldn't matter, as it should never
        # conflict with anything.  If something *does* conflict with
        # EOF, we'd want to know about it.  So, EOF has the lowest
        # precedence.
        self._acceptor_precedences[eof_acceptor] = -1
        eof_acceptor.add_empty_transition(end)

        self._nfa = nfa.Nfa(start, self._acceptor_rules.keys())
        self._eof_rule = eof_rule

    def lex(self, input_str):
        """Break an input stream into tokens.

        Yields tokens from the input stream, for each token whose rule specifies
        emitted=True.
        """
        source = charsource.RewindSource(input_str)
        while True:
            acceptors, match = self._nfa.longest_match(source)

            # If there are multiple possibilities, choose the one with
            # highest precedence.
            acceptor = max(acceptors, key=lambda acc: self._acceptor_precedences[acc])
            token = self._acceptor_rules[acceptor]

            if token is self._eof_rule:
                break

            assert len(match) > 0
            if token.emitted:
                yield Token(self._acceptor_rules[acceptor].name, match)

    def lex_file(self, open_file):
        """Break a file into tokens."""
        for token in self.lex(charsource.chars_in_file(open_file)):
            yield token
