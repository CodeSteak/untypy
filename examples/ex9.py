from typing import Optional, Union, Literal, Tuple
import untypy


X = Literal['x']
O = Literal['o']
Empty = Literal['-']

Player = Union[X, O]
Mark = Union[X, O, Empty]

Game = list[list[Mark]]

Coordinate = Literal[0, 1, 2]


def gameFull(game: Game) -> bool:
    for column in game:
        for cell in column:
            if cell == '-':
                return False
    return True


def checkWinner(game: Game) -> Optional[Player]:
    # rows
    for y in range(0, 3):
        if game[0][y] in ['x', 'o'] and game[0][y] == game[1][y] == game[2][y]:
            return game[0][y]

    # columns
    for x in range(0, 3):
        if game[x][0] in ['x', 'o'] and game[x][0] == game[x][1] == game[x][2]:
            return game[x][0]

    # Diagonal \
    if game[0][0] in ['x', 'o'] and game[0][0] == game[1][1] == game[2][2]:
        return game[0][0]

    # Diagonal /
    if game[2][0] in ['x', 'o'] and game[2][0] == game[1][1] == game[0][2]:
        return game[2][0]

    return None


def placePlayer(game: Game, x: Coordinate, y: Coordinate, player: Player) -> None:
    game[x][y] = player


def gameToString(game: Game) -> str:
    out = ""
    for y in range(0, 3):
        out += f"|{game[0][y]}|{game[1][y]}|{game[2][y]}|\n"

    return out


def getMove(player: Player) -> Tuple[int, int]:
    s = input(f"Player {player} place your move: <x> <y>").strip().split(' ', maxsplit=2)
    if len(s) != 2:
        error("Format: <x> <y>")
    try:
        x = int(s[0])
        y = int(s[1])

        return (x, y)
    except ValueError:
        error("x and y must be a valid int.")


def error(msg: str) -> None:
    raise Exception(msg)


def halfMove(game: Game, player: Player) -> bool:
    print(gameToString(game))
    (x, y) = getMove(player)

    # Note: Contract Violation if entered is outside of range
    placePlayer(game, x, y, player)

    winner = checkWinner(game)
    if winner is not None:
        print(f"\nWinner is {winner}.")
        return True

    if gameFull(game):
        print("Game Over: Draw")
        return True

    return False

def fullGame() -> None:
    game = [['-', '-', '-'], ['-', '-', '-'], ['-', '-', '-']]
    while not halfMove(game, 'x') and not halfMove(game, 'o'):
        pass

if __name__ == '__main__':
    untypy.enable()
    fullGame()