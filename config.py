import os 
dir_path = os.path.dirname(os.path.realpath(__file__))
public_url = "https://phonebot.rxinformatics.net:8443"
wss_url = "wss://phonebot.rxinformatics.net:8443"
tts_url = "http://localhost:5001"
stt_url = "http://localhost:5002"
llm_url = "http://localhost:5003"
grading_url = "http://localhost:5004"
syntax_url = "http://localhost:5005"
exllama_url = "http://localhost:5006"
phonecall_recordings_directory = os.path.join(dir_path, 'recordings')
if not os.path.exists(phonecall_recordings_directory):
    os.mkdir(phonecall_recordings_directory)
word_recordings_directory = os.path.join(dir_path, 'soundfiles')
model_directory = os.path.join(dir_path, 'models')
frontend_directory = os.path.join(dir_path, 'frontend')


