## Beartype

Checked nur darauf, ob die methoden vorhanden sind. Anzahl der Argumente wird ebenfalls geprüft.
```python
from typing import Protocol, runtime_checkable

from beartype import beartype


@runtime_checkable
class Inter(Protocol):
    def fun(self, b : int) -> None:
        pass

class Concrete:
    @beartype
    def fun(self, a : str) -> None:
        pass

@beartype
def foo(c : Inter) -> None:
    c.fun(42)


foo(Concrete())
```

```
@beartyped fun() parameter a="42" violates type hint <class 'str'>, as value "42" not str.
```

```python
class Concrete:
    @beartype
    def notfun(self) -> None:
        pass
```
```python
 @beartyped foo() parameter c=<__main__.Concrete object at 0x7f9bdab1b940> violates type hint <class '__main__.Inter'>, as value <__main__.Concrete object at 0x7f9bdab1b940> not <protocol "__main__.Inter">.
```

Note: `@runtime_checkable` ermöglicht dieses checking mit `isinstanceof`

## enforce

Protocol gibt es erst seit Python 3.8 see (PEP 544). Hat Enforce aber schon Probleme bei Vererbung.

```python
@enforce.runtime_validation
class Inter:
    def fun(self, b: int) -> None:
        pass

@enforce.runtime_validation
class Concrete(Inter):
    def fun(self, b : int) -> None:
        pass

@enforce.runtime_validation
def foo(c: Inter) -> None:
    c.fun(42)


foo(Concrete())
```
```
Argument 'c' was not of type <class '__main__.Inter'>. Actual type was Concrete.
```

## pytypes

Protocol gibt es erst seit Python 3.8 see (PEP 544).

```python
from pytypes import typechecked
@typechecked
class Inter:
    def fun(self, b: int) -> None:
        pass

@typechecked
class Concrete(Inter):
    def fun(self, b : str) -> None:
        pass

@typechecked
def foo(c: Inter) -> None:
    c.fun("42") # No error
    c.fun(42) # Expected: Tuple[str] Received: Tuple[int]

foo(Concrete()) 
```

## typeguard

```python
from typing import *
from typeguard import typechecked

@typechecked
class Inter(Protocol):
    def fun(self, b : int) -> None:
        pass

@typechecked
class Concrete:
    def fun(self, b : str) -> None:
        pass

@typechecked
def foo(c : Inter) -> None:
    c.fun(42)


foo(Concrete())
```
```
TypeError: type of argument "b" must be str; got int instead
```


