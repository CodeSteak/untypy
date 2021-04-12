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

## Was nutzen andere Python Libs:
 - Bearlib: Scheint kein wrapping zu machen. Erreicht O(1) für listen, dadurch, dass nur stichprobenartig überprüft wird
 - 