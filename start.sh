uvicorn --host 0.0.0.0 --port 80 app:app &
uvicorn --host 127.0.0.1 --port 5001 tts:app &
uvicorn --host 127.0.0.1 --port 5002 stt:app &
uvicorn --host 127.0.0.1 --port 5003 llm:app &
