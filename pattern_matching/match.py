class match:
    """ Create a pattern-matching function
    
    Supports the following pattern types:
      * Placeholder
      * Range
      * Callable
      * Literal, with limitations

    Supports the following result types:
      * Callable
      * Literal

    Parameters:
      * amount: int
          Number of arguments to match on.
      * patcall: bool (keyword-only)
          Accept callable patterns if True, otherwise treat as literal. You usually won't need to disable this.
      * retcall: bool (keyword-only)
          Accept callable return values if True, otherwise treat as literal. You usually won't need to disable this.

    Limitations:
      * Literal patterns cannot be slice objects or subtypes thereof.
    """
    def __init__(self, amount: int = 1, *, patcall: bool = True, retcall: bool = True):
        self.amount = amount
        self.patcall = patcall
        self.recall = retcall
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
        self.patterns.append((pattern, result))
        self.creating_pattern = None

    def match_apply(values):
        """ Search for a match and apply the corresponding result """
        if len(values) != self.amount:
            raise TypeError("Invalid amount of values for match")

        for pattern, result in self.patterns:
            if self.patcall and callable(pattern):
                is_match = bool(pattern(*values))
            else:
                is_match = bool(self.pattern_matches(pattern, values))

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
    def pattern_matches(patterns, values):
        """ Test if a value matches a (non-callable) pattern """
        for pattern, value in zip(patterns, values):
            if pattern == slice(None, None, None):
                # this is the catch-all pattern, [:]
                continue

            if isinstance(pattern, slice):
                # this is a range pattern, [a:b]
                lower = pattern.start
                upper = pattern.stop

                if lower is None and value > upper:
                    return False

                elif upper is None and value < lower:
                    return False

                if not lower <= value <= upper:
                    return False

            elif pattern != value:
                return False

        return True
