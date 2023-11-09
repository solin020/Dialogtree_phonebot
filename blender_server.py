import os
import shlex
import subprocess
import time

# Using port 8080 doesn't work on Colab
HOST = "0.0.0.0:5413"
PATH_TO_SEARCH_SERVER = "./ParlAI_SearchEngine/search_server.py"

assert os.path.exists(PATH_TO_SEARCH_SERVER), (f"Incorrect path {PATH_TO_SEARCH_SERVER}")

command = ["python", "-u", shlex.quote(PATH_TO_SEARCH_SERVER), "serve", "--host", HOST]
command_str = " ".join(command)
p = subprocess.Popen(command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

# Wait a bit before the next cell to let a lot of the potential errors happen.
time.sleep(3)

