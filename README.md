#Microservices
ANNA consists of the following microservices
##phonebot_tts
This is the text to speech server, located in tts.py. 
This service can be started by running "systemctl start service phonebot_tts"

##phonebot_stt
This is the speech to text server, located in stt.py
This service can be started by running "systemctl start service phonebot_stt"

##phonebot_llm
This is the large language model conversation partner server, located in llm.py
This service can be started by running "systemctl start service phonebot_llm"

##phonebot
This service can be started by running "systemctl start service phonebot_gateway".
It makes use of call_state.py. call_state.py contains the class CallState, whose objects
each control one ongoing phonecall. app.py can spawn multiple of these in response to simultaneous phonecalls, allowing ANNA
to talk to multiple people at once (though this multi-talking is still tightly limited by system resources).
CallState  contains the conversation script in its method "bot_initiated script", invoked whenever ANNA
rings the patient.
It also has a stub method "patient_initiated_script", used if the patient themselves rings ANNA,
currently this just redirects to bot_initiated script but we may create a unique script for this situation later.
The conversation script can request that the tts say something using its function "self.say(quote)". It can also play soundfiles
located in the soundfiles folder using the function "self.say(file=filename)". It can ask a question
using "response = self.ask(quote, **options)". This triggers ANNA to enter listening mode after she has made her statement.
She must be given a listening mode option. If await_silence=True, she will wait until her conversation partner has stopped talking.
If stopword_list=['Yes', 'Yeah'], she will wait until she hears her partner say those word. If wait_time=30, she will wait 30 seconds
for the patient to respond and then immediately move on. Multiple of these options can be combined. She will continue once the first option has happened, i.e., patient has gone silent, patient has said yes, or finally, 30 seconds have passed. minimum_turn_time=5 is an additional option
that prevents ANNA from moving on too early, overriding the other listening mode options.
ANNA will then ask the stt service for a transcript of what the patient has said. self.get_response() gives a history of ANNA's
conversation to the llm service to get a conversationally appropriate reply to say to the patient.

##psql

ANNA uses a postgres database to store its data.
Full setup is not included with ANNA, end users are expected to provide their own postgres database.
End users can specify where the database is by the following .env file parameters
DBHOST: hostname where the postgres server is running
DBUSER: username for ANNA to use when logged in to postgres (I recommend 'anna')
DBNAME: name of the database ANNA stores its data in (I also recommend 'anna')
DBPASSWORD: password for ANNA's user

The end user will need to set up this in advance, with commands such as

    CREATE DATABASE $DBNAME;
    CREATE USER $DBUSER WITH PASSWORD '$DBPASSWORD';
    GRANT ALL PRIVILEGES ON DATABASE $DBNAME TO USER $DBUSER;

with the appropriate substitutions provided.

database.py contains code for storing ANNA's records in a postgres database. 
Running
    $python database.py
will initialize the tables ANNA needs. This only needs to be run once, on install.

##clas
This microservice grades syntax. It is in the docker image clas:latest

##coherence
This microservice grades large language model coherence and also grades the memory tests. It is located in the docker image coherence:latest




#Setting up the .env file
The .env file must be written by the end user. It contains sensitive information that is local to the installation.
The following parameters must be provided:

USERNAME: the username required to log into ANNA's web portal
PASSWORD: the password required to log into ANNA's web portal

ACCOUNTSID: the twilio accountsid for the twilio number linked to ANNA
AUTHTOKEN: the twilio authtoken for the twilio number linked to ANNA

DBHOST: hostname where the postgres server is running
DBUSER: username for ANNA to use when logged in to postgres (I recommend 'anna')
DBNAME: name of the database ANNA stores its data in (I also recommend 'anna')
DBPASSWORD: password for ANNA's user

#setting up the frontend
running ./generate_client.sh must be run to reinitialize the typescript client the frontend uses if you ever edit app.py

