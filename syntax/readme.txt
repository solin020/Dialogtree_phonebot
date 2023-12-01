INSTALLATION

Change directories into package.

> cd clas_update

Create a python virtual environment.

> python -m venv env

Activate virtual environment.

> source env/bin/activate

Install python dependencies.

> pip install -r requirements.txt

Install graphviz if you want the Constituency Tree grapher to work. How to do this varies by system. For OSX it is:

> brew install graphviz

USAGE

$python depth.py --allennlp INPUT_ENGLISH_TEXT_FILE --output OUTPUT_DIRECTORY [--stats] [--graph]

--stats: save by-sentence of parsed english text into file $OUTPUT_DIRECTORY/stats.csv

--graph: print out constituency and dependency trees graphs for each sentence in the text into $OUTPUT_DIRECTORY/sentence_diagrams.pdf

