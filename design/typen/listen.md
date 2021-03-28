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
Bei der Übergabe wird die Liste durch iteriert und gechecked und Callables etc. werden gewrapped.

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
    def foo(self, f : list[Callable[[int], str])
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

# Was nutzen andere Python Libs:
...