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

# TODO:
#   - Hypothesis strategy to generate patterns and values
import pytest

from match import match, __matchresult__


## Testing utils

def assert_raises_many(exc, spec):
    for func, args, kwargs in spec:
        with pytest.raises(exc):
            func(*args, **kwargs)

def test_assert_raises_many():
    def raise_exc(e, msg=''):
        raise e(msg)
    assert_raises_many(ValueError, [
        (raise_exc, (ValueError,), {}),
        (raise_exc, (ValueError, 'hi'), {}),
        (raise_exc, (ValueError,), {'msg': 'hi'}),
    ])


## Basic behavioral tests

def test_slicepattern_1():
    """ Test 1-parameter slice-based patterns """
    f = (
        match()
            [None]  ('invisible')
            [12:52] ('really big, but not too big')
            [1]     ('unified')
            [7:]    ('seven or more')
            [:0]    ('too small and creepy')
            [:4]    ('small, like a bird')
            [:]     ('i dunno')
    )

    assert f(None) == 'invisible'
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

    bad_values = ['qt', dict, dict()]
    assert_raises_many(TypeError, [(f, (val,), {}) for val in bad_values])

    f = match()[3]('three')
    with pytest.raises(ValueError):
        f(4)
    with pytest.raises(TypeError):
        f(4,5)


def test_retcall():
    """ Test the retcall functionality """
    import math

    safelog = (match()
        [0] (1.0)
        [1:] (math.log)
        [:0] (math.nan))
    assert safelog(0) == 1.0
    assert abs(safelog(2) - math.log(2)) < 1e05
    assert safelog(-1) is math.nan

    weird1 = (match (retcall=False)
        ['sum'] (sum)
        ['any'] (any)
        [:]     (str))
    assert weird1('sum') is sum
    assert weird1('any') is any
    assert weird1(123)   is str

    weird2 = (match ()
        ['sum'] (sum)
        ['any'] (any)
        [:]     (str))
    with pytest.raises(TypeError, match='unsupported operand type'):
        # trying to call sum('sum')
        weird2('sum')
    assert weird2('any') == True
    assert weird2(123) == '123'


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

    weird1 = (match (patcall=False)
        [sum] ('sum')
        [any] ('any')
        [:]   ('other'))
    assert weird1(sum) == 'sum'
    assert weird1(any) == 'any'
    assert weird1(123) == 'other'

    weird2 = (match()
        [sum] ('sum')
        [any] ('any')
        [:]   ('other'))
    assert weird2([1,2]) == 'sum'
    assert weird2([-1,1]) == 'any'
    assert weird2([0,0]) == 'other'
    assert_raises_many(TypeError, [
        # trying to call sum(sum)
        (weird2, (sum,), {}),
        # trying to call sum(any)
        (weird2, (any,), {}),
        # trying to call sum(123)
        (weird2, (123,), {}),
    ])


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
        match().pattern_matches(slice(None,None,3), [None])



## Individual internal components

def test_getitem():
    m = match(2)[:,:]
    assert m.creating_pattern == (slice(None), slice(None))

    m = match()[:]
    assert m.creating_pattern == slice(None)

    m = match()[:,]
    assert m.creating_pattern == (slice(None),)

    # Error if wrong pattern size
    m = match(2)
    with pytest.raises(TypeError):
        m[:]
    with pytest.raises(TypeError):
        m[:,:,:]

    # Error if trying to create a pattern while already creating a pattern
    m = match()[:]
    with pytest.raises(ValueError):
        m[:]

    # Error if result is empty (see test_add_pattern)
    m = match()
    with pytest.raises(TypeError):
        m[:]()


def test_add_pattern():
    m = match()
    m.add_pattern(3, (3,))
    assert m.patterns[0] == (3, 3)

    # This is confusing and asymmetric, i hate it
    m = match()
    m.add_pattern((3,), (3,))
    assert m.patterns[0] == ((3,), 3)
    m.add_pattern((slice(None),), (3,))
    assert m.patterns[1] == ((slice(None),), 3)
    m.add_pattern(slice(None), (3,))
    assert m.patterns[2] == (slice(None), 3)

    m = match()
    m.add_pattern(lambda x: x+1, (__matchresult__,))
    m.add_pattern(lambda x: x+1, (__matchresult__, lambda x: x/10))
    # Error if __matchresult__ used incorrectly
    with pytest.raises(ValueError):
        m.add_pattern(lambda x: x+1, ((__matchresult__,),))
    with pytest.raises(ValueError):
        m.add_pattern(lambda x: x+1, ((__matchresult__, 1, 2),))

    # Error if result is empty
    m = match()
    with pytest.raises(TypeError):
        m.add_pattern(slice(None), ())


def test_get_match_result():
    m = match()
    # "Exact" matches always return bool
    assert m.get_match_result((1,), slice(None)) == True
    assert m.get_match_result((1,), 1) == True
    # "Called" matches return the result of the call
    assert m.get_match_result(([-1, 1],), sum) == 0


def test_get_call_result():
    m = match()
    m.get_call_result(('hello',), __matchresult__, 'this will be returned') == 'this will be returned'
    m.get_call_result(('hello',), (__matchresult__, len), 'this will not be returned') == len('this will not be returned')
    m.get_call_result(('hello',), len, 'this will not be returned') == len('hello')
    m.get_call_result(('hello',), 'this will be returned', 'this can be anything!') == 'this will be returned'


def test_match_apply():
    # TODO
    pass


def test_check_range_pattern():
    #assert     match.check_range_pattern(slice(None), 3)
    assert not match.check_range_pattern(slice(5), 10)
    assert     match.check_range_pattern(slice(5), 5)
    assert not match.check_range_pattern(slice(5), 5, include_upper=False)
    assert not match.check_range_pattern(slice(5,None), 1)
    assert     match.check_range_pattern(slice(0, 5), 3)
    assert     match.check_range_pattern(slice(0, 5), 0)
    assert     match.check_range_pattern(slice(0, 5), 5)
    assert not match.check_range_pattern(slice(0, 5), 5, include_upper=False)
    assert not match.check_range_pattern(slice(0, 5), 10)
    assert not match.check_range_pattern(slice(0, 5), -5)
    assert     match.check_range_pattern(slice('a', 'c'), 'b')
    assert not match.check_range_pattern(slice('0', '9'), 'b')
    assert     match.check_range_pattern(slice('0', '9'), '9')
    assert not match.check_range_pattern(slice('0', '9'), '9', include_upper=False)


def test_pattern_matches():
    # TODO
    pass


## Silly tests for timing and demo of capabilities

def test_patcall_complicated(benchmark):
    """ Test the patcall functionality by implementing a naive Fibonacci calculator """
    fib_match = (match()
        [:0] (0)
        [1]  (1)
        [:]  (lambda n: fib_match(n-1) + fib_match(n-2)))

    benchmark(fib_match, 10)


def test_perf_baseline(benchmark):
    """ Equivalent imperative code performance, to see match() overhead """
    def fib_py(n):
        if n <= 0:
            return 0
        if n == 1:
            return 1
        return fib_py(n-1) + fib_py(n-2)

    benchmark(fib_py, 10)
