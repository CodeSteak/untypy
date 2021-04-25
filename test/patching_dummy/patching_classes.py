class A:
    def __init__(self, y: int):
        self.y = y

    def add(self, x: int) -> int:
        return x + self.y
