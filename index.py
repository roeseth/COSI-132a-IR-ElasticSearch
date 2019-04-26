import json
import re
import time

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from elasticsearch_dsl import Index, Document, Text, Keyword, Date, Integer, Completion
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import tokenizer, analyzer
from elasticsearch_dsl.query import MultiMatch, Match

# corpus file name
corpus_file = 'films_corpus.json'

# index name
index_name = 'wiki_film_index'

# Connect to local host server
connections.create_connection(hosts = ['127.0.0.1'])

# Create elasticsearch object
es = Elasticsearch()

# Define appropriate analyzers
# for all fields except numeric fields, using casefolding + stopwords list + snowball stemmer
my_analyzer = analyzer('custom',
                       tokenizer = 'standard',
                       filter = ['lowercase', 'stop', 'snowball'])


# Define document mapping (schema) by defining a class as a subclass of Document.
# This defines fields and their properties (type and analysis applied).
class Movie(Document):
    text = Text(analyzer = my_analyzer)
    title = Text(analyzer = my_analyzer)
    language = Text(analyzer = my_analyzer)
    country = Text(analyzer = my_analyzer)
    director = Text(analyzer = my_analyzer)
    location = Text(analyzer = my_analyzer)
    starring = Text(analyzer = my_analyzer)
    # data in time and runtime fields are pre-processed
    time = Date()
    runtime = Integer()
    categories = Text(analyzer = my_analyzer)

    # override the Document save method to include subclass field definitions
    def save(self, *args, **kwargs):
        return super(Movie, self).save(*args, **kwargs)


# Populate the index
def buildIndex():
    """
    buildIndex creates a new film index, deleting any existing index of
    the same name.
    It loads a json file containing the movie corpus and does bulk loading
    using a generator function.
    """
    film_index = Index(index_name)
    film_index.document(Movie)
    if film_index.exists():
        film_index.delete()  # Overwrite any previous version
    film_index.create()

    # Open the json film corpus
    with open(corpus_file, 'r', encoding = 'utf-8') as data_file:
        # load movies from json file into dictionary
        movies = json.load(data_file)
        size = len(movies)

    # Action series for bulk loading with helpers.bulk function.
    # Implemented as a generator, to return one movie with each call.
    # Note that we include the index name here.
    # The Document type is always 'doc'.
    # Every item to be indexed must have a unique key.
    def actions():
        # mid is movie id (used as key into movies dictionary)
        for mid in range(1, size + 1):
            yield {
                "_index": index_name,
                "_type": 'doc',
                "_id": mid,
                "title": movies[str(mid)]['Title'],
                "text": movies[str(mid)]['Text'],
                "starring": movies[str(mid)]['Starring'],
                "runtime": movies[str(mid)]['Running Time'],
                "language": movies[str(mid)]['Language'],
                "country": movies[str(mid)]['Country'],
                "director": movies[str(mid)]['Director'],
                "location": movies[str(mid)]['Location'],
                "time": movies[str(mid)]['Time'],
                "categories": movies[str(mid)]['Categories']
            }

    helpers.bulk(es, actions())


def test_analyzer(text, analyzer):
    """
    a tester
    :param text: a string
    :param analyzer: the analyzer you defined
    :return: list of tokens processed by analyzer
    """
    output = analyzer.simulate(text)
    return [t.token for t in output.tokens]


def run_test_cases():
    """
    a test case, for debug purpose
    :return: none
    """
    title = "2.0"
    direc = ["Shan'kar"]
    star = ["Rajinikanth", "Aks'hay Kumar", "Amy Jackson", "Sudhanshu Pandey"]
    runtime = 147
    country = ["India"]
    lan = ["Tamil"]
    time = [1981]
    loc = ["Chennai"]
    text = "2.0 is a 2018 Indian Tamil-language sci-fi action film by S. Shan'kar"
    cats = ["2010s Tamil-language films",
            "2010s action films",
            "2010s science fiction action fcilms",
            "2010s science fiction films"]
    print(test_analyzer(title, my_analyzer))
    print(test_analyzer(direc, my_analyzer))
    print(test_analyzer(star, my_analyzer))
    print(test_analyzer(country, my_analyzer))
    print(test_analyzer(lan, my_analyzer))
    print(test_analyzer(loc, my_analyzer))
    print(test_analyzer(text, my_analyzer))
    print(test_analyzer(cats, my_analyzer))


# command line invocation builds index and prints the running time.
def main():
    start_time = time.time()
    # run_test_cases()
    buildIndex()
    print("=== Built index in %s seconds ===" % (time.time() - start_time))


if __name__ == '__main__':
    main()
