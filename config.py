import os 
from starlette.config import Config
secret_config = Config("phonebot/.env")
dir_path = os.path.dirname(os.path.realpath(__file__))
public_url = "https://phonebot.rxinformatics.net:8443"
wss_url = "wss://phonebot.rxinformatics.net:8443"
tts_url = "http://localhost:5001"
stt_url = "http://localhost:5002"
llm_url = "http://localhost:5003"
grading_url = "http://localhost:5004"
syntax_url = "http://localhost:5005"
exllama_url = "http://localhost:5006"
word_recordings_directory = os.path.join(dir_path, 'word_recordings')
call_recordings_directory = os.path.join(dir_path, 'call_recordings')
sounds_directory = os.path.join(dir_path, 'sounds')
model_directory = os.path.join(dir_path, 'models')
frontend_directory = os.path.join(dir_path, 'frontend')
nlp_resources_directory = os.path.join(dir_path, 'nlp_resources')
gateway_username = secret_config('USERNAME')
gateway_password = secret_config('PASSWORD')
account_sid = secret_config('ACCOUNTSID')
auth_token = secret_config('AUTHTOKEN')
db_username=secret_config('DBUSERNAME')
db_password=secret_config('DBPASSWORD')
db_host=secret_config('DBHOST')
db_name=secret_config('DBNAME')
