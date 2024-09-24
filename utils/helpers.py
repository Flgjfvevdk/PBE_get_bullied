import os

def getenv(name:str) -> str:
    val = os.getenv(name)
    if val is None:
        raise Exception(f"ENV variable {name} is not set!")
    return val