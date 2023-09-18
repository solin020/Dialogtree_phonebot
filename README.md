ANNA consists of the following microservices
-text to speech, in tts.py. 
This service can be started by running "systemctl start service phonebot_tts"

-speech to text, in stt.py
This service can be started by running "systemctl start service phonebot_stt"

-a large language dialog model which can be queried to respond to a turn of a conversation, in llm.py
This service can be started by running "systemctl start service phonebot_llm"

-a control server, in app.py
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

-a postgres database
database.py contains code for storing ANNA's records in a postgres database.

-a syntax grader, located in the docker image clas:latest

-an llm and memory test grader, located in the docker image coherence:latest

