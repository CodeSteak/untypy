def __init__(self):
    print("init")

def __getattr__(name):
    print("__getattr__")

def __setattr__(self, key, value):
    print("__setattr__")

def yolo():
    pass

print("xxx")