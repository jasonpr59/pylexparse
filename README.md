# pylexparse
A generic lexer and parser interface for Python.

## Goal
The goal is to create a generic lexer and parser interface for Python.  Clients will specify a (somewhat) arbitrary grammar, and pylexparse will lex and parse arbirary textual input according to the grammar and return a parse tree.

## Progress
So, far, the library can:
  * Interpret a Regular Expression string as a `Pattern`.
  * Transform a `Pattern` into an NFA (Nondeterministic Finite Automaton).
  * Run an NFA against a string and decide whether the string matches.

In other words, the library is currently a somewhat underpowered regex matcher:
```
$ ./pylexparse.py match '[bm]e*(at|f{4})' beef
False
$ ./pylexparse.py match '[bm]e*(at|f{4})' beeeeeeeeffff
True
$ ./pylexparse.py match '[bm]e*(at|f{4})' meat
True
$ ./pylexparse.py match '[bm]e*(at|f{4})' beaffff
False
```

## Personal Comments
I'm writing this library "from scratch," and for my own edification.  I'm deliberately ignoring a lot of great libraries.  I don't want to deprive myself the fun of implementing functionality that they provide!
