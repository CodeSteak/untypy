# Listen

## Möglichkeiten:

### V1
Bei der Übergabe wird die Liste durch iteriert und gechecked.

Pro: 
- Einfach
- Fehler werden sofort erkannt.

Contra:
- Komplexe Typen wie Callables können nicht gechecked werden, wenn sie als Liste übergeben werden


### V2
Bei der Übergabe wird die Liste durch iteriert und gechecked, Callables etc. werden gewrapped. 
Das Ergebnis wird in eine neue Liste geschrieben, welche dann übergeben wird.

Pro:
- Komplexe Typen können gechecked werden

Contra:
- Wenn eine andere Codestelle eine Referenz auf diese Liste hat und diese verändert, werden veränderungen in 
  kopierten Liste nicht sichtbar.
  
### V3

Bei der Übergabe wird die Liste gewrapped und erst beim zugriff überprüft und in diesem Schritt 
auch elemente gewrapped.

Pro:
- O(1)
- Callables möglich

Contra:
- Komplexität

# Bsp:
```python
class Foo:
    def foo(self, f : list[Callable[[int], str]) -> None:
        self.f = f

    def bar(self):
        for f in self.f:
            f()

foo = Foo()
lst = []

foo.foo(lst)
lst.append(lambda x: print('hello world'))

foo.bar()
# => V1 'hello world' (aber kein Typechecking)
# => V2 '' aber Typechecking
# => V3 'hello world' ( + Typechecking)
# => V4 'hello world'
```

Problem: 
Wenn Refenzen gespeichert werden ist es keine "normale" liste. 

### V4

Bei der Übergabe werden in der Liste die Items ausgetauscht. 
Aus einem "normalen" Callable wird Wrapped-Callable.

```python

def a(lst : list[Callable[[Any], None]]):
  pass


def b(lst : list[Callable[[int], None]]):
  pass

lst = [...]
a(lst)
b(lst)
a(lst)
b(lst)
```
Bei einer trivialen Implementierung würde im Beispiel jedes Callable mehrfach gewrapped.

Lösung:
Typen müssen vereinigt werden können:
also z.B. Callable[[Any], None] + Callable[[int], None] --> Callable[[And[Any,int]], None]

Weiteres Problem:
Diese Lösung funktioniert nur, wenn es sich um "normale" Funktionen oder lambda expressions handelt.
Wenn andere Objekte, die Callable implementieren, gewrapt werden, können möglicherweise andere Funktionen
nicht mehr aufgerufen werden:

```python
class A:
  def __call__(self, *args, **kwargs):
    pass
    
  def something(self):
    pass

def foo(lst : list[Callable[[], None]]):
  pass
  
lst = [A()]
lst[0].something() # Okay
foo(lst)
lst[0].something() # Method Not Found
```

Idee 1: Nur einfache Funktionen wrappen.
Idee 2: getitem und setitem nutzen, um aufs innere Obj. zuzugreifen, jedoch kann es bei `type(lst[0])` zu problemen 
kommen, daher ungeeignet.
Idee 3: `__call__` von A überschreiben.
Idee 4: Dynamisch zur Laufzeit Subklasse von A erstellen, mit modifizietem `__call__`

##  Umsetzung in anderen Python Libs:

### BearType
(python 3.9.2 / beartype 0.6.0)

BearType úberprüft keine Callables als Argumente, daher werden diese auch nicht in Listen unterstützt:
```python
@beartype
def do_something(x: Callable[[int], str]):
    x(42)

@beartype
def wrong(x: int) -> int:
    return x

do_something(wrong) # Okay
```
Beim Typechecking von Listen wird jedem Funktionsaufruf zufällig ein Pfad verfolgt und überprüft:
```python
@beartype
def do_something(x: list[int]):
    pass

ok = 0
error = 0
iterations = 100
for i in range(0, iterations):
    try:
        do_something([1, 2, 3, 4, 5, 6, 7, 8, "nine", 10])
        ok += 1
    except:
        error += 1

print(f"Ok: {ok / iterations}") # Ok: 0.9
print(f"Error: {error / iterations}") # Error: 0.1
```

### Enforce
(python 3.6.0 / enforce 0.3.4)

Callables werden anhand der Signatur überprüft:
```python
@enforce.runtime_validation
def do_something(x: Callable[[int], str]):
    pass

@enforce.runtime_validation
def wrong(x: int) -> int:
    return x

do_something(wrong) # TypeError
```
Bei Lambda-Expressions kann nur "Callable" ohne weiter Argument-Typen angegeben werden.

Callables innerhalb von Listen führen immer zum Fehler:
```python
@enforce.runtime_validation
def do_something(x: List[Callable[[int], str]]):
    pass

@enforce.runtime_validation
def right(x: int) -> str:
    return str(x)

do_something([right]) # TypeError: sequence item 0: expected str instance, CallableMeta found
```

Listen werden scheinbar sequenziell überprüft:
```python
@enforce.runtime_validation
def do_something(x: List[int]):
    pass

do_something([1, 2, 3, 4, 5, 6, 7, 8, "nine", 10])  # Argument 'x' was not of type typing.List[int]. Actual type was typing.List[int, str].
```

### pytypes
(python 3.6.0 / pytypes 1.0b5)

Pytypes vergleicht signaturen von Callables:
```python
from typing import *

@typechecked
def do_something(x: Callable[[int], str]):
    pass

@typechecked
def actually_do_something(x: Callable[[int], str]):
  x(42)

@typechecked
def wrong(x: int) -> int: 
    return x

do_something(wrong) # TypeError
```
Lambda Expression werden gewrapped:
```python
do_something(lambda x: x) # Kein Fehler, da kein Aufruf.
actually_do_something(lambda x: x) # TypeError
```

Callables in Listen werden jedoch nicht auf dieselbe Art überprüft:
```python
@typechecked
def do_something(x: List[Callable[[int], str]]):
    pass

@typechecked
def right(x: int) -> str:
    return str(x)

do_something([right])
```
```
pytypes.exceptions.InputTypeError: 
  __main__.do_something
  called with incompatible types:
Expected: Tuple[List[Callable[[int], str]]]
Received: Tuple[List[function]]
```
Ansonsten finden typechecking in Listen auf allen Elementen statt:
```python
@typechecked
def do_something(x: List[int]):
    pass

do_something([1, 2, 3, 4, 5, 6, 7, 8, "nine", 10])
```
```
  called with incompatible types:
Expected: Tuple[List[int]]
Received: Tuple[List[Union[int, str]]]
```
In der Fehlermeldung wird der übergebene Typ richtig angegeben.

### Typeguard
(python 3.9.4 / typeguard 2.12.0 )

In Typeguard findet kein Wrapping statt:
```python
@typechecked
def do_something(x: Callable[[int], str]):
    x(42)
    pass

@typechecked
def wrong(x: int) -> int:
    return x

do_something(wrong) # Ok
```
Ansonsten finden typechecking in Listen auf allen Elementen statt:
```python
@typechecked
def do_something(x: List[int]):
    pass

do_something([1, 2, 3, 4, 5, 6, 7, 8, "nine", 10])
```
```
TypeError: type of argument "x"[8] must be int; got str instead
```


