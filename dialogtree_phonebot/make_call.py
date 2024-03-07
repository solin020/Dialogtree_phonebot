import requests
from config import public_url
import sys
phone_number = sys.argv[-2]
previous_rejects = sys.argv[-1]
print('here here!') 
requests.post(f'http://localhost:80/make-call', json=[phone_number, previous_rejects])
