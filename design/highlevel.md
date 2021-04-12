-- GROBE NOTIZEN ZUM DESIGN --

# Verwendung / Bootstraping

Bei anderen Python Bibliotheken (Welche?) zum Typechecking werden (Function-) Decorators verwendet. 
Dies hat den Nachteil, dass explizit alle Funktionen annotiert werden müssen.
```python
@typechecked
def foo(x : int) -> None:
    pass
```

Stattdessen wird in untypy ein anderer Ansatz verfolgt:
Die Bibliothek wird vor dem start des Programms einmalig aufgerufen und alle annotierten Funktion werden 
automatisch getypchecked. 
=> anfängerfreundlicher und ergodischer zu verwenden, da boiler-plate code reduziert wird.
 
```python
import untypy

def foo(x : int) -> None:
    pass 

if __name__ == '__name__':
    untypy.enable()
    ...
```
Beim Aufruf von ```enable``` wird der Call-Stack durchiteriert um das aufrufende Modul zu endecken.
Anschließend werden mittels Inspection alle annotierten Funktionen mit dem Typechecker gewrapped.

Alle Annotationen sind Optional, funktionen ohne Annotationen sind nicht vom Typechecking betroffen.  

(TODO) Werden nur einige Argumente der Funktion annotiert, schlägt enable fehl. So wird verhindert, dass
Annotionen vergessen wurden. 

Konsequenz hiervon ist, dass Funktionen ohne Return-Wert mit `None` annotiert werden müssen, 
da sonst der Rückgabe-Typ nicht überprüft werden kann.

## Klassen (TODO)

Wird bei der Inspection des eine Moduls Klasse entdeckt, so werden Methoden der Klassen ebenfalls gewrapped und
ausgetauscht.

Attribute der Klasse, welche ebenfalls annotiert werden können zu checken wäre vermutlich etwas zu komplex.
(AST-Edit) 
```python
class A:
    x: int
    y: int

    def foo(self):
        pass
```

## Submodule (TODO)
(Hint: Module vs. Packages)

Anschließend wird über ```sys.modules``` iteriert und alle Funktionen ( - / in Klassen) ebenfalls gewrapped.
Es werden ausschließlich Submodule verändert, um zu verhindern, dass Dependencies brechen, wenn diese andere
Annahmen zum Typechecken getroffen haben oder diese andere Typechecking-Bibliotheken verwenden.

Es muss ebenfalls möglich sein, mehrere Root-Module explizit angeben zu können, um sich flexibel auf andere Projektstrukturen
anpassen zu können.

## Checken nur zwischen Modulgrenzen (Maybe TODO)
Grober Ansatz hier: Mittels custom Import-Statement wird ein neues Modul erzeugt, welches Funktionen des Inneren, eigentlich 
importierten, Modul aufruft und Typechecked. 
Instanzen von Klassen werden ebenfalls gewrappt und rufen ihre innere Instanz auf.
Es wäre denkbar diese Klassen dynamisch zur Laufzeit zu erzeugen und zu cachen. 


# Interne Architektur

## Bildung des Typcheckers 

Fúr Type checking gibt es ein allgemeines Interface. 
```python

class ITypeChecker:
    def check(self, arg : T, ctx: IExecutionContext) -> T:
        ... 
```
Idee: Callables, Listen Etc. müssen gewrapped werden. `check` returned das zu Überprüfende `arg` oder die gewrappte
Version davon, welche dann an die "eigentliche" Implementierung übergeben werden soll.

Das `ctx`-Argument wird verwendet, um Typfehler auszulösen: Entweder direkt beim Aufruf (Einfache Type) oder später in
den gewrappen typen, sobald fehler festgestellt werden.

Im Fehlerfall wird eine Exception geworfen. (Mehr -> error.md)

ITypeChecker können auch verschachtelt werden. So verwendet z.B. der Checker für `list[int]` intern Checker für 
einfache Typen. Im Fehlerfall des inneren Checkers können Exeptions abgefangen werden und durch Informationen 
ergänzt werden. 

Um den passenden Typechecker für einen in der Methodendefinition Typ auszuwählen, 
wird eine globale List durch iteriert, jeder Checker (via `ITypeCheckerFactory`) kann auf eine Annotation
reagieren. Der erste passende Typechecker wird verwendet.


### Probleme des Wrappings:

Identität eines Python-Objektes bleibt nicht erhalten, wenn gewrapped wird:
```python
Y = lambda: 42

def foo(x : Callable[[], int]) -> bool:
    return x is Y


foo(Y)
```

Ohne typechecking returned `foo` `true`, mit typechecking wird `false` returned. 

Weiteres Bsp:
```python
class A:
    x : Callable[[], int]
    
    def register(self, x : Callable[[], int]) -> None:
        self.x = x

    def already_registred(self, x : Callable[[], int]) -> bool:
        return x is self.x

foo(Y)
```

Dieses Verhalten tritt jedoch nicht bei "gewöhnlichen" Objektes des Anweders auf, da diese nicht gewrapped werden.

Bei verwendung von `==` anstelle von `is` ist dieses Verhalten vermeidbar. (TODO: Double Check via Unittest)

<!-- Zuständigkeiten erleutern --


## Andere Libs:
### Typeguard:
Entweder: 
```
typeguard.importhook.install_import_hook()
```
- no code changes required in target modules

oder pro funktion via Decorator.