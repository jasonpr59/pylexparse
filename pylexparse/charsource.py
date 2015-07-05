"""Tools for getting and ungetting input characters."""

import collections

class GetPutSource(object):
    """An input source with getc() and ungetc() equivalents."""
    def __init__(self, iteratable):
        self._iterator = iter(iteratable)
        self._put_chars = collections.deque()

    def get(self):
        """Get the next character from the input stream."""
        if self._put_chars:
            return self._put_chars.pop()
        try:
            return next(self._iterator)
        except StopIteration:
            # None is our EOF.
            return None

    def put(self, char):
        """Put a character back onto the input stream.

        Characters are put back in LIFO order.
        """
        self._put_chars.append(char)


class RewindSource(object):
    """An input source that remembers what it has given up."""

    def __init__(self, iterable):
        self._source = GetPutSource(iterable)
        self._read = collections.deque()

    def __iter__(self):
        return self

    def next(self):
        return self.get()

    def get(self):
        """Return the next character."""
        char = self._source.get()
        self._read.append(char)
        return char

    def disown_first(self, num_to_forget):
        """Forget the least recently read characters, forever.

        Returns a string of the forgotten charcters.
        """
        disowned = (self._read.popleft() for _ in xrange(num_to_forget))
        # We use None as an EOF.
        return ''.join(char for char in disowned if char is not None)

    def rewind(self):
        """Put the read characters back in line to be read.

        The first (unforgotten) character to be read will now be the
        first character returned by get().
        """
        while self._read:
            self._source.put(self._read.pop())


def chars_in_file(file):
    """Yield each character in a file."""
    for line in file:
        for char in line:
            yield char
