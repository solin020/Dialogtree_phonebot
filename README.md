# Overview
DialogTree is a simple xml-directed LLM-powered dialog management system. In addition to using the backing LLM to generate the dialog that the user sees, it also uses said LLM to determine user intent and for named entity recognition, avoiding the need for complex NLP to extract these things from the user's responses.
### Nomenclature
In DialogTree, a **user**, who either needs questions answered and/or some tasks done on their behalf, communicates with the **system**, the script-directed AI who responds to them. The **system**, by asking questions of the **user**, accumulates information about them in the **context**, a python dictionary which stores strings of information, each organized under a **key**. 

The system's script is controlled by a file written in an XML subset language called **DialogTreeML**, defined in the file `dialogtree.dtd`. IDEs such as VSCODE can interpret `dialogtree.dtd` and help identify errors in any DialogTreeML files you write. In a DialogTreeML file, underneath the root node `<dialogtree>`, the system's dialog is divided into **destinations**, which may be named via the XML attribute `destinationname`. When a dialog with the system is started, it begins at the **starting destination**, the very first destination listed in the file. The system navigates to different sections of the dialog by **jumping** to a different **destination**. How jumping works varies depending on the destination type. 

`<state>` destinations print out a statement and then jump to a destination controlled by their `nextdestination` attribute. 

`<branch>` destinations ask the user a question and then jump to a new destination (and possibly preform other actions) depending on their answer.

In `<fullquestion>` destinations, it is the user asks the system a question, the inverse of `<branch>` destinations. These destinations can also jump to one of several other destinations once the user is done asking questions.

The `<goodbye>` destination prints a goodbye message before the user finishes their dialog with the system. It is a mandatory part of any script. It can always be jumped to by the special `destinationname` of `end`.

## Determining the answer to a question, or "Intent", in a `<branch>` desination
Often, when speaking to the user, you need to ask them questions which only have a few valid answers, like a yes/no question. But human language is very flexible, and yes or no answers can be conveyed in a great number of ways. Positive answers to a question like "Do you have any pets?" might be "yes", "yeah", "I have 2 cats", or "I do." and negative answers could be "no", "nope", "I used to have a dog", or "I don't have any". The user may also reply in a way we aren't able to respond to, like "I'm not sure what counts as a pet" or "I think I should get dogfood for my Beagle when I drop by the grocery store tonight". Writing code to properly parse all of the possible answers to these questions can be quite the challenge, but fortunately, modern LLMs such as ChatGPT are quite adept at this task straight out of the box. DialogTree provides a straightforward way to do this using the `<answerparse>` xml element. To explain, let's go through the example below.
```    
  <branch>
    <userquestion>
        Hi! I am your pet purchasing assistant. 
        Are you interested in purchasing a cat or a dog?
    </userquestion>
    <errorprompt>
        Explain to the user who just replied with this: 
          <response/> 

        to this question:
          <backprompt/>

        that you only know how to answer questions
        about advising them about cat or dog purchases and ask them if they want a cat or a dog.
    </errorprompt>
    <answerparse>
        Did the person who answered this:
          <response/>

        to this question:
          <backprompt/>

        want a cat, a dog, or something else?
        If cat, respond "cat". If dog, respond "dog". If anything else, respond "other".
        Say only one word.
    </answerparse>
    <jump answer="cat dog">
      <![CDATA[
      context["animal"] = answer
      if answer == "cat":
          with open("cats.txt") as f:
             context["breedinfo"] = f.read()
          return "catbreed"
      elif answer == "dog":
          with open("dogs.txt") as f:
              context["breedinfo"] = f.read()
          return "dogbreed"
      ]]>
    </jump>
  </branch>
```
This `<branch>` expect an answer of either "cat" or "dog", as determined by all
of the `answer` attributes on each `<jump>` element at the end (in this case only one).
The contents of `<userquestion>` are printed for the user to see.
Let's say that the user responds to this question with "I think I would like a german shepherd". Though to a human it is obvious they want a dog, this is pretty challenging for a traditional NLP system to answer. So we ask chatgpe. The contents of `<answerparse>`, with `<response/>` replaced with the user's response to the question and `<backprompt/>` replaced with the last question they were asked, is sent to our LLM.
> Did the person who answer this:
> 
> I think I would like a german shepherd
>
> to this question:
>
> Hi! I am your pet purchasing assistant.
> Are you interested in purchasing a cat or dog?
>
> want a cat, a dog, or something else?
> If cat, respond "cat". If dog, respond "dog", If anything else, respond "other".
> Say only one word.

If we're lucky, the LLM will respond "dog". A bit less lucky, the LLM will respond with something like "The user said they wanted a dog.". As these sorts of overly verbose answer is fairly common, DialogTree counts it as a "dog" response merely if the string for a valid answer, "dog", occurs anywhere in the LLM's response. If we're really unlucky, it'll give us a useless response like "They asked for a German Shepherd.", which DialogTree cannot parse. It can sometimes take quite a bit of artistic finessing of the prompt inside of `<answerparse>` to get the LLM to behave, so play around until you get satisfactory results. Note that LLMs will not always respond with the same answer to the same question, so just because the dialog tree worked fine one time doesn't mean it won't fail again. The answer to this problem is again, test, test test.
### Dealing with unusual responses
Sometimes, the user is going to answer in a question that our system just doesn't have any appropriate way to respond to. Let's say our user said "Oh, I need to buy food at the grocery store tonight." Our answerparse step fails to find an answer it can respond to, i.e "cat" or "dog", and instead jumps to `<errorprompt>`. The variables in `<errorprompt>` are filled out and this is sent to the LLM. This generates a clarification question for the user.

| **What is sent to the LLM**
```
Explain to the user who just replied with this:
Oh, I need to buy food at the grocery store tonight.

to this question:

Hi! I am your pet purchasing assistant.
Are you interested in purchasing a cat or a dog?


that you only know how to answer questions
about advising them about cat or dog purchases and ask them if they want a cat or a dog.

```

| **What the user sees**

> `SYSTEM` Hi! I am your pet purchasing assistant.
> Are you interested in a cat or dog?

> `USER` Oh, I need to buy food at the grocery store tonight.

> `SYSTEM` I'm here to assist with cat or dog purchases. Your statement about the grocery store doesn't include whether you're interested in a cat or dog. Would you like to get a cat or dog?


This loop of asking clarification questions will repeat until the user responds with something that the LLM can parse via `<answerparse>`

## Advancing the dialog and preforming actions with the `<jump>` element
Once the answer is parsed, it is sent to a `<jump>` element with a matching `answer` attribute. If the jump element needs to match multiple answers, separate them with spaces. Note that this requires that this requires that parsed answers be a single word. Inside of the `<jump>` element is an optional python function which is executed before jumping. Consider the example below.
```
<jump answer="allergic no" nextdestination="indoororoutdoor">
      <![CDATA[
      if answer=="allergic":
          context["allergy"] = answer
      else:
          context["allergy"] = "not allergic"
      ]]>
</jump>
``` 
Note the funky looking 
```
<![CDATA[
    *your code here*
]]>
```
structure wrapped around the python code. This CDATA annotation is necessary to 
prevent conflict between python and XML syntax.

If the user had previously replied "allergic" to the preceding question, 
this would get translated and executed as:
```
def jumpfunction(answer, context):
    context['allergy'] = answer
jumpfunction(answer='allergic', dialog.context)
```
allowing us to store the user's question into the context for later use.

In this example, the `nextdestination` attribute on the `<jump>` element leads
to an unconditional jump to the destination named `indooroutdoor`. If the logic to specify where to jump to next is more complicated than this, we can specify the destination name in the return value of the python function itself, as shown below.
```
<jump answer="cat dog">
      <![CDATA[
      context["animal"] = answer
      if answer == "cat":
          with open("cats.txt") as f:
             context["breedinfo"] = f.read()
          return "catbreed"
      elif answer == "dog":
          with open("dogs.txt") as f:
              context["breedinfo"] = f.read()
          return "dogbreed"
      ]]>
</jump>
```
This `<jump>` node will be triggered by either the answers "cat" or "dog"
and will jump to the destination "catbreed" for cats and "dogbreed" for dogs.

If it is necessary that the jump node instead accept a whole range of answers,
a function name can instead be passed via the `accept` attribute. This function
must return either a valu if accepted (possibly modified) or None if not. This function
must have the signature (answer, context) and be passed in the "functions" dict
given to the DialogTree object on initialization. An example is shown below

First, the python file:

```
import re
def match_zipcode(answer, context):
    if (zipcode:= re.match(r"\d{5}", answer)[0]):
        context["zipcode"] = zipcode
        return zipcode
    else:
        return None

dialog = Dialog(treefile="example.xml", functions={'match_zipcode': match_zipcode}, openai_key=openai_key, org_id=org_id, model="gpt-4")

```

Then, the `<jump>` element in the xml:

```
<jump accept="match_zipcode">
      <![CDATA[
      print("Your zipcode is: " + context["zipcode"])
      ]]>
</jump>
```

If the jump function is exceptionally complex, it is advisable to write the function
in a separate python file and link it to the `<jump>` element via the
`functionname` attribute. Like the accept function, the
 jump function has to be passed in the "functions" dict
given to the DialogTree object on initialization, with the corresponding key
in the dictionary matching that stated in the `functionname` attribute. The function's
signature is also  (answer, context). An example is shown below.

`example.py`
```
def catdog_jump(answer, context):
    context["animal"] = answer
    if answer == "cat":
        with open("cats.txt") as f:
            context["breedinfo"] = f.read()
        return "catbreed"
    elif answer == "dog":
        with open("dogs.txt") as f:
            context["breedinfo"] = f.read()
        return "dogbreed"

dialog = Dialog(treefile="example.xml", 
    functions={"catdog_jump": catdog_jump}, 
    openai_key=openai_key, 
    org_id=org_id, 
    model="gpt-4")
dialog.start()
```

`example.xml`
```
...
<jump answer="cat dog" functionname="catdog_jump"/>
...
```


## Answering the user's questions
Up until now in our example dialog tree, all questions have come from the system, determining what the user's situation and needs are. Now, having gathered all of the information it needed, the system is ready to answer the user's questions. This is accomplished using one of two choices of element, `<llmquestion-direct>` or `<llmquestion-indirect>` element. 

`<llmquestion-direct>` elements are simpler. They work very similarly to `<state>` elements, except instead of displaying their contents directly to the user, the contents are instead sent as a question to an llm and printed out for the user to see.
Consider below. At this point in the dialog, the user has specified that they only have indoor space for their dog
and they are allergic to dogs as well.

```
  <llmquestion-direct destinationname="recommendbreeddirect" nextdestination="end">
    Using the information on breeds of <context key="animal"/> provided here:
    
    <context key="breedinfo"/> 

    recommend a breed of dog to the user, given that they are <context key="allergy"/> to <context key="animal"/>
    and have <context key="livingspace"/> space for the animal. 
  </llmquestion-direct>
```

The LLM sees the below as its prompt, after the substiution process introduces context.
> Using the information on breeds of dog provided here:
> 
> German Shepherd, allergenic, outdoor  
> Standard Poodle, hypoallergenic, outdoor  
> Bichon Frise, hypoallergenic, indoor  
> Shiba inu, allergenic, indoor  
> 
> recommend a breed of dog to the user, given that they are not allergic to to dog and have indoor > space for the animal.

and the user sees the system's response as so:
> `SYSTEM` Based on your needs, a Bichon Frise would be the best choice 
since it is hypoallergenic and suitable for indoor spaces.

If instead we want to be a little more flexible about how we ask questions, we can instead
ask the user what question they want answered and provide that to the LLM in a prompt
using the `<llmquestion-indirect>` element, shown below.

```
  <llmquestion-indirect destinationname="recommendbreedindirect" nextdestination="end">
    <userquestion>
      I am ready to recommend a breed of <context key="animal"/> to you now. Ask me for a recommendation.
    </userquestion>
    <answerparse>
      Using the information on breeds of <context key="animal"/> provided here:
          <context key="breedinfo"/> 

      answer this user's question, given that they are <context key="allergy"/> to <context key="animal"/>
      and have <context key="livingspace"/> space for the animal. 
    </answerparse>
  </llmquestion-indirect>
```
First, the substituted contents of `<userquestion>` are printed out for the user.
Then, the user responds. Their response is then sent to `<answerparse>`, which is substituted,
and that is used to prompt the LLM. Finally, the LLM's response is printed. An example 
dialog exchange using `<llmquestion-indirect>` is shown below.

> `SYSTEM` I am ready to recommend a breed of dog to you now. Ask me for a recommendation.

> `USER` Do you think I should get a dog?

> `SYSTEM` You should consider a Standard Poodle.

Both of these elements take a `nextdestination` attribute to indicate to DialogTree
where to jump to next.

## Using other LLMs
Dialogtree is configured to use OpenAI models by default. If you would like to use
another LLM approach, you will need to subclass the `Dialog` class in dialogtree.py.
Two things need to be changed.
A `complete(self, prompt:str)->str` function must be provided, which takes a string
which is given to the LLM and returns the LLMs response.
an `init(self, treefile:str, functions: dict[str, Callable], *args, **kwargs)` function must also be overwritten, providing whatever arguments are necessary to instantiate your LLM.