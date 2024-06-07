from dotenv import load_dotenv, main
import os

def Connect():
    load_dotenv()
    token = os.getenv('TOKEN')
    org = os.getenv('ORG')
    bucket = os.getenv('BUCKET')
    return token, org, bucket