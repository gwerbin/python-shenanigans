class match:
    """ Create a pattern-matching function
    
    Supports the following pattern types:
      * Placeholder (:)
      * Literal, with limitations

    Supports the following result types:
      * Literal

    Parameters:
      * amount: int
          Number of arguments to match on

    Limitations:
      * Literal patterns cannot be slice objects or subtypes thereof.
    """

    def __init__(self, *, amount=1):
        self.amount = amount

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

    def __call__(self, *values):
        if self.creating_pattern is not None:
            if len(values) != 1:
                raise ValueError("Pattern must only return one value")

            self.patterns.append(
                (self.creating_pattern, values[0])
            )

            self.creating_pattern = None
            return self

        if len(values) != self.amount:
            raise ValueError("Invalid amount of values for match")

        for pattern, result in self.patterns:
            if self.pattern_matches(pattern, values):
                return result

        raise ValueError("No matching pattern found.")

    @staticmethod
    def pattern_matches(patterns, values):
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
