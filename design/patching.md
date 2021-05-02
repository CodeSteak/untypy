# Patchen von Funktionen

## Beartype

Innerhalb des Dekorators:
(https://github.com/beartype/beartype/blob/b0576e80b686b512c27d07228112b2b09fb85e43/beartype/_decor/main.py#L156)
Erstellt 'string' source code wrapper. 
Führt dann Eval aus 
(https://github.com/beartype/beartype/blob/b0576e80b686b512c27d07228112b2b09fb85e43/beartype/_util/func/utilfuncmake.py#L239)
Das Eval geschieht auf str Basis: 
```python
def make_func(
    # Mandatory arguments.
    func_name: str,
    func_code: str,
    ...
):
    ...
```
Vorteile:
    - Performance (Past zu den Designconstraints der Lib)

Nachteile: 
 - Binding nicht so einfach möglich. => Literals oder userdefined Contract-Checking problematisch, 
   wegen potentiellen scope probelemen.

## Enforce
Decorator werden auf die Klassendeklaration angewendet. In der Readme steht folgendes Bsp:
```python
@runtime_validation
class DoTheThing(object):
    def __init__(self):
    self.do_the_stuff(5, 6.0)

    def do_the_stuff(self, a: int, b: float) -> str:
        return str(a * b)
```

Klassen werden mit GenericPoxy gewrapped:
(https://github.com/RussBaz/enforce/blob/caf1dc3984c595a120882337fa6c2a7d23d90201/enforce/decorators.py#L135)

`isinstance` funktioniert überraschenderweise aber dennoch:
```python
@enforce.runtime_validation
class Root:
    pass

@enforce.runtime_validation
class A(Root):
    pass

@enforce.runtime_validation
class B:
    pass


print(type(A())) # <class '__main__.A'>
print(type(B())) # <class '__main__.B'>

print(isinstance(A(), A)) # True
print(isinstance(A(), Root)) # True
print(isinstance(A(), B)) # False
```

Frage: <br\>
Funktioniert Vererbung auch, wenn patching ohne Decorator, weil dann A's Root noch das alte Root zeigen könnte?
```python
class Root:
    pass

@enforce.runtime_validation
class A(Root):
    pass

Root = enforce.runtime_validation(Root)

print(isinstance(A(), Root)) # True
```
=> Funktioniert dennoch.

Detail:
Klassenkonstanten werden ebenfalls in neuen GenericProxy kopiert (https://github.com/RussBaz/enforce/blob/caf1dc3984c595a120882337fa6c2a7d23d90201/enforce/decorators.py#L138)

## pytypes

Monkey Patching von individuellen Methoden innerhalb der Klasse. (https://github.com/Stewori/pytypes/blob/95d58a30a8ddb665500d8e88b13a94e0e0f76373/pytypes/typechecker.py#L928)

Beim (ersten) Versuch dieses Ansatzes in untypy, konnte auf `self` innerhalb eines Callables nicht zugegriffen werden.

Pytypes nutzt Clojure statt Callables

## enforce

Same as pytypes (https://github.com/agronholm/typeguard/blob/abcaa5d6f34eaddd4f5cd1ab1c16c853554eaf6c/src/typeguard/__init__.py#L920)

