# Functionality to test:
#  Patterns
#    - Placeholder
#    - Range
#    - Callable
#    - Literal
#  Results
#    - Callable
#    - Literal
#  Options
#    - amount
#    - patcall
#    - retcall
#  Exceptions
#    - Number of arguments
#  Extensions
#    - whatever https://pypi.org/project/whatever/
#    - macropy https://pypi.org/project/macropy3/
#  Edge cases?

# Things to consider:
#   - Hypothesis strategy to generate patterns and values?
import pytest

from match import match


def assert_raises_many(exc, spec):
    for func, (args, kwargs) in spec:
        with pytests.raises(exc):
            func(*args, **kwargs)


def test_slicepattern_1():
    """ Test 1-parameter slice-based patterns """
    f = (
        match()
            [12:52] ('really big, but not too big')
            [7:]    ('seven or more')
            [:5]    ('small, like a bird')
            [1]     ('unified')
            [:0]    ('too small and creepy')
            [:]     ('i dunno')
    )

    assert f(100) == 'i dunno'
    assert f(13) == 'really big, but not too big'
    assert f(9) == 'seven or more'
    assert f(6) == 'i dunno'
    assert f(5) == 'small, like a bird'  # ranges are **inclusive**
    assert f(4) == 'small, like a bird'
    assert f(1) == 'unified'
    assert f(0) == 'too small and creepy'  # ranges are **inclusive**
    assert f(-20) == 'too small and creepy'

    bad_values = ['qt', None, dict, dict()]
    assert_raises_many(TypeError, [(f, (val,), {}) for val in bad_values])


def test_retcall():
    """ Test the retcall functionality """
    import math

    safelog = (
        match()
            [0] (1.0)
            [1:] (math.log)
            [:0] (math.nan)
    )

    assert safelog(0) == 1.0
    assert abs(safelog(2) - math.log(2)) < 1e05
    assert safelog(-1) is math.nan


def test_patcall():
    """ Test the patcall functionality """
    def not_string(x):
        return not isinstance(x, str)

    def raises(exc, message):
        def do_raise(x):
            raise exc(message(x) if callable(message) else message)
        return do_raise

    intaddexpr = (
        match()
            [not_string]                   (raises(TypeError, 'Input must be a string'))
            [str.isdigit]                  (int)
            [re.compile(r'\s*+\s*').split] (lambda x: sum(map(calc, x)))  # wrap it in a lambda to protect from the parser; TODO: match.recall
            [:]                            (raises(ValueError, 'Not a valid integer: {}'.format))
    )

    assert intaddexpr('-12') == -12
    assert intaddexpr('3 + 4') == 7
    assert_raises_many(TypeError, [
        (intaddexpr, (None,), {}),
        (intaddexpr, (1230,), {})
    ])
    assert_raises_many(ValueError, [
        (intaddexpr, ('a + b',), {}),
        (intaddexpr, ('a',), {}),
    ])


def test_init():
    """ Test the match() constructor itself """
    assert_raises_many(TypeError, [
        (match, (-1,), {}),
        (match, (1, False, False), {}),
        (match, (1, False,), {retcall=False}),
    ])
