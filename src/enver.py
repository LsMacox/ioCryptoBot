from dotenv import load_dotenv
import os

load_dotenv()


def getenv(key: str):
    return os.getenv(key)
