import os
from dotenv import load_dotenv

load_dotenv()

creds = os.getenv("CREDS")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")