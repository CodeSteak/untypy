import untypy

untypy.enable()

from typing import *
import io

AppendOnlyFile = Annotated[io.TextIOBase, lambda file: file.mode == 'a',
                           'A File that is opend with mode "a".']


def log(file: AppendOnlyFile, message: str) -> NoReturn:
    file.write(message + "\n")


file = open("mylogfile", "w")
log(file, "Programm Started")
