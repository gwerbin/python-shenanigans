__all__ = [
    'match',
    '__matchresult__',
]


# TODO: figure out if Sphinx has something like this, just a placeholder for now
def doc_private(func):
    """ Flag a function as 'private' for documentation purposes """
    return func


class match:
    """ Create a pattern-matching function
    
    Supports the following pattern types:
      * Placeholder
      * Range
      * Callable
      * Literal, with limitations

    Supports the following result types:
      * Callable
      * Literal, with limitations

    Parameters:
      * amount: int
          Number of arguments to match on.
      * patcall: bool (keyword-only)
          Accept callable patterns if True, otherwise treat as literal. You usually won't need to disable this.
      * retcall: bool (keyword-only)
          Accept callable return values if True, otherwise treat as literal. You usually won't need to disable this.

    Limitations:
      * Literal patterns cannot be slice objects or subtypes thereof.
      * Literal patterns cannot be callable objects unless patcall=False.
      * If a literal pattern or literal result is a tuple, it must have a trailing comma:
            match()[(1,2)] will be interpreted as a 2-parameter match on integers 1 and 2
            match()[(1,2),] will be interpreted as a 1-parameter match on the tuple (1,2)
      * Literal results cannot be callable objects unless retcall=False.
    """
    def __init__(self, amount: int = 1, *, patcall: bool = True, retcall: bool = True):
        self.amount = amount
        if not isinstance(amount, int) or amount < 1:
            raise ValueError('Invalid amount, must be a positive integer')

        self.patcall = patcall
        self.retcall = retcall
        self.patterns = []
        self.creating_pattern = _notcreating

    def __getitem__(self, patterns):
        if self.creating_pattern is not _notcreating:
            raise ValueError('A pattern is already being created, cannot create another one.')

        pattern_has_incorrect_size = (
            (isinstance(patterns, slice) and self.amount != 1)
            or (isinstance(patterns, tuple) and self.amount != len(patterns))
        )

        if pattern_has_incorrect_size:
            raise TypeError("Pattern has incorrect size")

        self.creating_pattern = patterns
        return self

    def __call__(self, *values):
        if self.creating_pattern is _notcreating:
            # Call the match function for real; look for matches and apply the correct result
            return self.match_apply(values)
        else:
            # This was called after [] -- we now need to add the return value for the pattern
            self.add_pattern(self.creating_pattern, values)
            return self

    def add_pattern(self, pattern, result):
        """ Add a (pattern, result) pair """
        if len(result) == 0:
            raise TypeError('No result given.')

        if len(result) == 1:
            # Tuples are for user convenience when len > 1,
            # but when len == 1 assume that we should unwrap
            result = result[0]

        if isinstance(result, tuple) and result[0] is __matchresult__:
            if len(result) != 2:
                raise ValueError('__matchresult__ must occur by itself, or in a length-2 tuple.')

        self.patterns.append((pattern, result))
        self.creating_pattern = _notcreating

    @doc_private
    def get_match_result(self, values, pattern):
        if self.patcall and callable(pattern):
            # returns whatevers, need not be bool (this lets you use __matchresult__)
            match_result = pattern(*values)
        else:
            # returns bools
            match_result = self.pattern_matches(pattern, values)
        return match_result

    @doc_private
    def get_call_result(self, values, result, match_result):
        if result is __matchresult__:
            result = match_result
        elif isinstance(result, tuple) and result[0] is __matchresult__:
            result = result[1](match_result)

        if self.retcall and callable(result):
            result = result(*values)

        return result

    @doc_private
    def match_apply(self, values):
        """ Search for a match and apply the corresponding result """
        if len(values) != self.amount:
            raise TypeError("Invalid amount of values for match.")

        for pattern, result in self.patterns:
            match_result = self.get_match_result(values, pattern)
            if match_result:
                return self.get_call_result(values, result, match_result)

        raise ValueError("No matching pattern found.")

    @doc_private
    @staticmethod
    def check_range_pattern(pattern, value, include_upper=True):
        """ Test a slice/range pattern """
        lower = pattern.start
        upper = pattern.stop

        if lower is not None and upper is not None:
            if include_upper:
                return lower <= value <= upper
            else:
                return lower <= value < upper

        if lower is None and upper is not None:
            if include_upper:
                return value <= upper
            else:
                return value < upper

        if lower is not None and upper is None:
            return value >= lower

    @doc_private
    def pattern_matches(self, pattern, values):
        """ Test if a value matches a (non-callable) pattern """
        if not isinstance(pattern, tuple):
            # This lets us iterate over a "length 1" pattern where they wrote [:] or [4] instead of [:,] or [4,]
            # Note that they still have to write [(1,2),] due to ambiguity in the logic
            # TODO: move this inside match.check_range_pattern()?
            pattern = (pattern,)

        for term, value in zip(pattern, values):
            if term == slice(None, None, None):
                # this is the catch-all pattern, [:]
                continue

            if isinstance(term, slice):
                if term.step is not None:
                    # ???
                    raise NotImplementedError('A range pattern with a step value has no meaning (yet).')

                # this is a range pattern, [a:b]
                if not self.check_range_pattern(term, value):
                    return False

            elif term != value:
                return False

        return True


class __matchresult__:
    def __new__(self):
        raise TypeError('__matchresult__ cannot be insantiated.')


class _notcreating:
    def __new__(self):
        raise TypeError('__matchresult__ cannot be insantiated.')