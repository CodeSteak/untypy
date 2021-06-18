TODO
====

## Features

### Prio A
```
[\] Neue Abstraktion für Protokoll, um Listen, Dicts, Import zu abstrahieren
[ ] typing.Annotated:
    - range - Callable condition - Callable typeresolution
[ ] VScode Integration
```

### Prio B

```
[ ] TypeVar Bounds (mit Wrapping vorallem für Protocolls) 
[ ] typing.Type
[X] import only mode
[ ] inspect.stack() durch sys._getframe() ersetzen.. Location source Lazy
[ ] Instance Of Support (Überschreibbar)
[ ] Wrapped Generics (Aktuell Falsche Fehlermeldungen)
```

### Prio C

```
[ ] Utils für Contracts
[ ] Protocols Refactor, ProtocolWrapper Types werden dynamisch erstellt.
[ ] Async / Await
[ ] Better Protocol Errors (Mail)
```

## Task

```
[ ] Readme Updaten mit Features
[ ] Examples
[ ] Python Docs
```

## Bugs

```
[ ] Unittest: Callable inside Protocol
[ ] `__future__` Annotations & Generics.
[ ] Mehre Protocols in Union können aktuell überscheiden
[ ] _exec_module_patched nur bei __main__, ansonsten Error.
[ ] kein error bei import * (Unsupported)
[ ] List (großes L) wird nicht supported
```