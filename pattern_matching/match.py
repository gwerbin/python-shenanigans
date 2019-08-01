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
        self.creating_pattern = None

    def __getitem__(self, patterns):
        pattern_has_incorrect_size = (
            (isinstance(patterns, slice) and self.amount != 1)
            or (isinstance(patterns, tuple) and self.amount != len(patterns))
        )

        if pattern_has_incorrect_size:
            raise ValueError("Pattern has incorrect size")

        self.creating_pattern = patterns
        return self

    def add_pattern(self, pattern, result):
        """ Add a (pattern, result) pair """
        if len(result) == 1:
            # Tuples are for user convenience when len > 1,
            # but when len == 1 assume that we should unwrap
            result = result[0]
        self.patterns.append((pattern, result))
        self.creating_pattern = None

    def match_apply(self, values):
        """ Search for a match and apply the corresponding result """
        if len(values) != self.amount:
            raise TypeError("Invalid amount of values for match")

        for pattern, result in self.patterns:
            if self.patcall and callable(pattern):
                is_match = bool(pattern(*values))
            else:
                if not isinstance(pattern, tuple):
                    # so they don't have to write [:,] or [4,], but they still have to write [(1,2),]
                    pattern = (pattern,)
                is_match = self.pattern_matches(pattern, values)

            if is_match:
                if self.retcall and callable(result):
                    result = result(*values)
                return result

        raise ValueError("No matching pattern found.")
    
    def __call__(self, *values):
        if self.creating_pattern is not None:
            # This was called after [] -- we now need to add the return value for the pattern
            self.add_pattern(self.creating_pattern, values)
            return self
        else:
            # Call the match function for real; look for matches and apply the correct result
            return self.match_apply(values)

    @staticmethod
    def check_range_pattern(pattern, value, include_upper=True):
        """ Test a slice/range pattern """
        lower = pattern.start
        upper = pattern.stop

        if lower is not None and upper is not None:
            if include_upper:
                return lower <= value < upper
            else:
                return lower <= value <= upper

        if lower is None and upper is not None:
            if include_upper:
                return value <= upper
            else:
                return value < upper

        if lower is not None and upper is None:
            return value >= lower

    def pattern_matches(self, patterns, values):
        """ Test if a value matches a (non-callable) pattern """
        for pattern, value in zip(patterns, values):
            if pattern == slice(None, None, None):
                # this is the catch-all pattern, [:]
                continue

            if isinstance(pattern, slice):
                if pattern.step is not None:
                    # ???
                    raise NotImplementedError('A range pattern with a step value has no meaning (yet)')

                # this is a range pattern, [a:b]
                if not self.check_range_pattern(pattern, value):
                    return False

            elif pattern != value:
                return False

        # fell through a catch-all pattern at the end
        return True
