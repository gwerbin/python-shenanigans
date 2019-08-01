# Pattern matching in Python

## Example

```python
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
