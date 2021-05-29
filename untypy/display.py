class IndicatorStr:
    ty: str
    indicator: str

    def __init__(self, ty: str, indicator: str = ""):
        while len(indicator) < len(ty):
            indicator += " "

        self.ty = ty
        self.indicator = indicator

    def __add__(self, other):
        return IndicatorStr(self.ty + other.ty, self.indicator + other.indicator)

    def join(self, lst):
        return IndicatorStr(
            self.ty.join(map(lambda s: s.ty, lst)),
            self.indicator.join(map(lambda s: s.indicator, lst)),
        )
