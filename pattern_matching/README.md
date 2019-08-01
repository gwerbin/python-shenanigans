# Pattern matching in Python

## What is it?

Create functions using pattern matching, a common feature of functional programming languages like ML, Haskell, et al.

The `pattern_matching` module contains the `match` object, which you use to define a "matching function". A matching function works like a regular function with positional-only arguments. So once a matching function has been created, you can use it like any other function.

What makes a matching function special is how it's defined:

```python
is_mom = (match()
    ['Janet'] ('Hi mom!')
    [:]       ("I'm looking for my mom..."))
```

How to read this code:
  - `is_mom` accepts exactly 1 positional argument
  - `is_mom('Janet')` returns `'Hi mom!'`
  - `is_mom` with any other argument returns `"I'm looking for my mom..."`.

Compare this to a two possible plain-Python versions:

```python
def is_mom_1(name):
    return 'Hi mom!' if name == 'Janet' else "I'm looking for my mom..."

def is_mom_2(name):
    if name == 'Janet':
        return "Hi mom!"
    return "I'm looking for my mom..."
```

The `match` version emphasizes the relationships between pieces of data, while the plain-Python versions put greater emphasis on the procedure of checking for and returning data.

## Example

```python
from pattern_matching import match

is_py37 = (
    match (amount=3)
        [3, 7, :] (True)
        [:, :, :] (False)
)
is_py37.__doc__ = """ Check if a python version is 3.7 """


assert is_py37(3, 7, 4)
assert is_py37(3, 7, 0)

assert not is_py37(3, 6, 9)
assert not is_py37(2, 7, 16)

import sys
print(is_py37(*sys.version_info[:3]))
```

## API

### `pattern_matching`

#### *class* `pattern_matching.match(amount=1)`

Create a pattern-matching function

**Parameters**:
  * `amount: int` - Number of arguments to match on.

Supports the following pattern types:
  * Placeholder (`:`)
  * Literal, with limitations

Supports the following result types:
  * Literal

Limitations:
  * Literal patterns cannot be slice objects or subtypes thereof, because `:` is special Python syntax that represents a slice

## How does it work?

Python's magic syntactical treatment of the `__getitem__` method and `slice` objects.
