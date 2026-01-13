import os

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN", "no token set")
OWNER_ID = int(os.getenv("OWNER", "-1"))
