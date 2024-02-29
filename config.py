import os 
from starlette.config import Config
secret_config = Config("dialogtree_phonebot/.env")
dir_path = os.path.dirname(os.path.realpath(__file__))
public_url = "https://openemr.rxinformatics.net"
wss_url = "wss://openemr.rxinformatics.net"
main_port='54321'
tts_port = '54322'
stt_port = '54323'
tts_url = f"http://localhost:{tts_port}"
stt_url = f"http://localhost:{stt_port}"
sounds_directory = os.path.join(dir_path, '../sounds')
model_directory = os.path.join(dir_path, '../models')
account_sid = secret_config('ACCOUNTSID')
auth_token = secret_config('AUTHTOKEN')
openai_key=secret_config('SECRETKEY')
org_id=secret_config('ORGID')
twilio_phone_number='+17637106226'