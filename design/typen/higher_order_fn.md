# Higher Order Functions

HOF werden bei übergabe als Argument oder rückgabe zusätzlich gewrapped.
Analog zu Funktionen in Modulen.

Mehrfach wrapping dadurch möglich wenn z.B.
```python
class A:
    pass

class B(A):
    pass


def foo() -> Callable[[A],None]:
    return lambda x : print(42)

def bar(f : Callable[[B],None]) -> None:
    f(...)


bar(foo())
```
Jenach Art der Contract-Violation kann so eine Code-Stelle verantwortlich gemacht werden.


## Problem durch diesen Ansatz:

```python

def foo(x) -> Callable[[int],None]:
    x


f = lambda x: None
for x in range(1000):
    f = foo(f)
```
Hier wird f 2000 mal gewrapped. Ein derartiger Fall ist auch durch rekursion denkbar.

Mögliche Lösung und Optimierung:
(TODO?): Wenn bereits gewrapped mit selber Signatur ist ein weiteres Wrapping überflüssig.
(Q: Wer ist verantwortlich? Oberer, Unterer, Egal?)