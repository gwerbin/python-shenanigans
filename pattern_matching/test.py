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
    for func, args, kwargs in spec:
        with pytest.raises(exc):
            func(*args, **kwargs)


def test_slicepattern_1():
    """ Test 1-parameter slice-based patterns """
    f = (
        match()
            [12:52] ('really big, but not too big')
            [1]     ('unified')
            [7:]    ('seven or more')
            [:0]    ('too small and creepy')
            [:4]    ('small, like a bird')
            [:]     ('i dunno')
    )

    assert f(100) == 'seven or more'
    assert f(13) == 'really big, but not too big'
    assert f(9) == 'seven or more'
    assert f(6) == 'i dunno'
    assert f(2) == 'small, like a bird'
    assert f(4) == 'small, like a bird'  # ranges are **inclusive**
    assert f(3) == 'small, like a bird'
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
    friendly_isdigit = (
        match()
            [lambda x: isinstance(x, str)] ('Its a string :)')
            [:]                            ('Not a string :(')
    )

    assert friendly_isdigit('hello') == 'Its a string :)'
    assert friendly_isdigit(None) == 'Not a string :('
    assert friendly_isdigit(25) == 'Not a string :('


def test_patcall_complicated(benchmark):
    """ Test the patcall functionality by implementing an integer calculator """
    import re

    def not_string(x):
        return not isinstance(x, str)

    def raises(exc, message):
        def do_raise(x):
            raise exc(message(x) if callable(message) else message)
        return do_raise

    plus = re.compile(r'\s*\+\s*')
    parens = re.compile(r'\(\s*(.+?)\s*\)')

    #def print_result(f):
    #    i = 0 
    #    def _f(*args, **kwargs):
    #        result = f(*args, **kwargs)
    #        nonlocal i
    #        i += 1
    #        print(i, f.__name__, repr(result), repr(args), repr(kwargs))
    #        return result
    #    return _f

    #@print_results
    def process_parens(x):
        return intaddexpr(parens.sub(lambda m: str(intaddexpr(m[1])), x))

    #@print_results
    def process_plus(x):
        return intaddexpr(str(sum(map(intaddexpr, plus.split(x)))))

    #@print_results
    def process_minus(x):
        return -intaddexpr(x[1:])

    intaddexpr = (
        match()
            [not_string]            (raises(TypeError, 'Input must be a string'))
            [str.isdigit]           (int)
            #[parens.search]         (lambda x: parens.sub(lambda m: str(intaddexpr(m[0][1:-1])), x))
            #[plus.search]           (lambda x: sum(map(intaddexpr, plus.split(x))))
            #[lambda x: x[0] == '-'] (lambda x: -intaddexpr(x[1:]))
            [parens.search]         (process_parens)
            [plus.search]           (process_plus)
            [lambda x: x[0] == '-'] (process_minus)
            [:]                     (raises(ValueError, 'Not a valid integer: {}'.format))
    )

    #assert intaddexpr('-12') == -12
    #assert intaddexpr('3 + 4') == 7
    assert intaddexpr('-(2 + 1) + -3') == -6
    assert intaddexpr('-( 2 + 1 ) + -3') == -6
    assert_raises_many(TypeError, [
        (intaddexpr, (None,), {}),
        (intaddexpr, (1230,), {})
    ])
    assert_raises_many(ValueError, [
        (intaddexpr, ('a + b',), {}),
        (intaddexpr, ('a',), {}),
    ])

    benchmark(intaddexpr, '-( 2 + 1 ) + -3')


def test_perf_baseline(benchmark):
    """ Equivalent imperative code performance, to see match() overhead """
    import re
    plus = re.compile(r'\s*\+\s*')
    parens = re.compile(r'\(\s*(.+?)\s*\)')
    def intaddexpr(expr):
        if not isinstance(expr, str):
            raise TypeError('Input must be a string')
        if expr.isdigit():
            return int(expr)
        if parens.search(expr):
            return intaddexpr(parens.sub(lambda m: str(intaddexpr(m[1])), expr))
        if plus.search(expr):
            return intaddexpr(str(sum(map(intaddexpr, plus.split(expr)))))
        if expr[0] == '-':
            return -intaddexpr(expr[1:])
        ValueError('Not a valid integer: {}'.format)

    benchmark(intaddexpr, '-( 2 + 1 ) + -3')


def test_init():
    """ Test the match() constructor itself """
    with pytest.raises(ValueError):
        match(-1)

    assert_raises_many(TypeError, [
        (match, (1, False, False), {}),
        (match, (1, False,), {'retcall': False}),
    ])


def test_rangepattern_impl():
    """ Test the implementation of slice patterns """
    assert match.check_range_pattern(slice(1,None), 1) is True
    assert match.check_range_pattern(slice(1,None), 2) is True
    assert match.check_range_pattern(slice(1,None), -1) is False
    assert match.check_range_pattern(slice(None,1), 1) is True
    assert match.check_range_pattern(slice(None,1), 2) is False
    assert match.check_range_pattern(slice(None,1), -1) is True
    assert match.check_range_pattern(slice(None,1), 1, include_upper=False) is False
    with pytest.raises(NotImplementedError):
        # result of check_range_pattern with slice(None,None,None) is "undefined behavior"
        match().pattern_matches([slice(None,None,3)], [None])
