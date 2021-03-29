# Error

Work In Progress.

Grob: 
- Es gibt einen `UnpytyError`-Typ, dieser beinhaltet eine Liste von `UnpytyFrame`s. 
- Die Frames werden mithilfe des Contexts erzeugt.
- Mithilfe der Frames soll nachvollziehbar gemacht werden wie der Fehler aufgetreten ist.
  Bsp: Eine Funktion `foo` gibt ein `Callable` (Wrapped) zurück, dieses gibt eine Liste (Wrapped) zurück,
  beim Zugriff auf ein Listen-Element wird festgestellt, dass im Callable eine falsche Liste erzeugt wurde.
  
Ein UnpytyFrame beinhaltet folgende Infos: (??)
 - Verantwortliche Callsite?  (TODO: Bessere Abtrennung)
 - Callsite des Auftretens?  (TODO: Bessere Abtrennung)
 - Informationen des verletzten Typs?
 - Zusätzliche Extra Infos? 

Das Context Object behaltet folgende Infos:
 - Parent Context
 - Verantwortliche Callsite
 - Argument-Name / Postion das in diesem Context überprüft wird.
 - Oder die Information, dass es sich um den Return-Wert handelt


# Refactor:
 - Bessere Trennung von Verantwortliche Callsite zu tatsächlicher Callsite
 - Werden Zwei Typen von UnpytyFrame benötigt? Oder kann Context Recycled werden?
