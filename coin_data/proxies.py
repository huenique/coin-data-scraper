import os

from dotenv import load_dotenv

load_dotenv()

PROXIES = os.getenv("PROXIES", "").split(",")
