"""
This module implements a (partial, sample) query interface for elasticsearch movie search. 
You will need to rewrite and expand sections to support the types of queries over the fields in your UI.

Documentation for elasticsearch query DSL:
https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html

For python version of DSL:
https://elasticsearch-dsl.readthedocs.io/en/latest/

Search DSL:
https://elasticsearch-dsl.readthedocs.io/en/latest/search_dsl.html
"""

import re
from flask import *
from index import Movie
from pprint import pprint
from elasticsearch_dsl import Q
from elasticsearch_dsl.utils import AttrList
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.analysis import tokenizer, analyzer

app = Flask(__name__)

# Initialize global variables for rendering page
tmp_text = ""
tmp_title = ""
tmp_star = ""
tmp_min = ""
tmp_max = ""
tmp_director = ""
tmp_lan = ""
tmp_country = ""
tmp_loc = ""
tmp_minyear = ""
tmp_maxyear = ""
tmp_cats = ""
gresults = {}

# index name var
index_name = 'wiki_film_index'


# display query page
@app.route("/")
def search():
    return render_template('page_query.html')


# display results page for first set of results and "next" sets.
@app.route("/results", defaults = {'page': 1}, methods = ['GET', 'POST'])
@app.route("/results/<page>", methods = ['GET', 'POST'])
def results(page):
    global tmp_text
    global tmp_title
    global tmp_star
    global tmp_min
    global tmp_max
    global tmp_director
    global tmp_lan
    global tmp_country
    global tmp_loc
    global tmp_minyear
    global tmp_maxyear
    global tmp_cats
    global gresults

    # convert the <page> parameter in url to integer.
    if type(page) is not int:
        page = int(page.encode('utf-8'))
        # if the method of request is post (for initial query), store query in local global variables
    # if the method of request is get (for "next" results), extract query contents from client's global variables  
    if request.method == 'POST':
        # if has query, strip() all whitespace
        text_query = request.form['query'].strip()
        star_query = request.form['starring'].strip()

        mintime_query = request.form['mintime'].strip()
        if len(mintime_query) != 0:
            mintime_query = int(mintime_query)

        maxtime_query = request.form['maxtime'].strip()
        if len(maxtime_query) != 0:
            maxtime_query = int(maxtime_query)

        director_query = request.form['director'].strip()
        lan_query = request.form['language'].strip()
        country_query = request.form['country'].strip()
        loc_query = request.form['location'].strip()

        minyear_query = request.form['minplottime'].strip()
        if len(minyear_query) != 0:
            minyear_query = int(minyear_query)

        maxyear_query = request.form['maxplottime'].strip()
        if len(maxyear_query) != 0:
            maxyear_query = int(maxyear_query)

        cats_query = request.form['categories'].strip()

        # update global variable template data
        tmp_text = text_query
        tmp_star = star_query
        tmp_min = mintime_query
        tmp_max = maxtime_query
        tmp_director = director_query
        tmp_lan = lan_query
        tmp_country = country_query
        tmp_loc = loc_query
        tmp_minyear = minyear_query
        tmp_maxyear = maxyear_query
        tmp_cats = cats_query
    else:
        # use the current values stored in global variables.
        text_query = tmp_text
        star_query = tmp_star
        mintime_query = tmp_min
        maxtime_query = tmp_max
        director_query = tmp_director
        lan_query = tmp_lan
        country_query = tmp_country
        loc_query = tmp_loc
        minyear_query = tmp_minyear
        maxyear_query = tmp_maxyear
        cats_query = tmp_cats

    # store query values to display in search boxes in UI
    shows = {}
    shows['text'] = text_query
    shows['star'] = star_query
    shows['maxtime'] = maxtime_query
    shows['mintime'] = mintime_query
    shows['director'] = director_query
    shows['lan'] = lan_query
    shows['country'] = country_query
    shows['loc'] = loc_query
    shows['minyear'] = minyear_query
    shows['maxyear'] = maxyear_query
    shows['cats'] = cats_query
    # keep a copy of original text query, in case cull out explicit phrases later
    full_text_query = text_query

    # Create a search object to query our index 
    s = Search(index = index_name)

    # Build up your elasticsearch query in piecemeal fashion based on the user's parameters passed in.
    # The search API is "chainable".
    # Each call to search.query method adds criteria to our growing elasticsearch query.
    # You will change this section based on how you want to process the query data input into your interface.

    # set flag to default to indicate all terms have been matched
    all_matched = True

    # compile a Regex pattern to extract explicit phrases enclosed by ""
    pattern = re.compile(r'(?:\B\")(.*?)(?:\b\")')
    phrases = pattern.findall(text_query)
    # get the rest free terms
    text_query = pattern.sub('', text_query).strip()

    # First doing conjunctive search over multiple fields (title and text) using the text_query and phrases passed in
    if len(text_query) + len(phrases) > 0:
        # save deep copies for disjunctive search later
        tmp_s = s.__copy__()
        tmp_phrases = phrases.copy()

        # conjunctive search for text_query AND phrases, with boosted field weight
        if len(text_query) > 0:
            s = s.query('multi_match', query = text_query, type = 'cross_fields', fields = ['title^2', 'text'],
                        operator = 'and')
        while len(phrases) > 0:
            s = s.query('multi_match', query = phrases.pop(), type = 'phrase_prefix', fields = ['title^2', 'text'])

        # if conjunctive search has no result, doing disjunctive ( text_query OR phrases )
        if s.count() == 0:
            # indicate not all terms are matched
            all_matched = False

            if len(text_query) > 0:
                q = Q('multi_match', query = text_query, type = 'cross_fields', fields = ['title^2', 'text'],
                      operator = 'or')
            else:
                q = Q('multi_match', query = tmp_phrases.pop(), type = 'phrase_prefix', fields = ['title^2', 'text'])

            while len(tmp_phrases) > 0:
                q |= Q('multi_match', query = tmp_phrases.pop(), type = 'phrase_prefix', fields = ['title^2', 'text'])

            s = tmp_s.query(q)

    # search for multiple fields using chained query (AND)
    if len(mintime_query) > 0:
        s = s.query('range', runtime = {'gte': mintime_query})

    if len(maxtime_query) > 0:
        s = s.query('range', runtime = {'lte': maxtime_query})

    if len(minyear_query) > 0:
        s = s.query('range', runtime = {'gte': minyear_query})

    if len(maxyear_query) > 0:
        s = s.query('range', runtime = {'lte': maxyear_query})

    if len(star_query) > 0:
        s = s.query('match', starring = star_query)

    if len(director_query) > 0:
        s = s.query('match', director = director_query)

    if len(lan_query) > 0:
        s = s.query('match', language = lan_query)

    if len(country_query) > 0:
        s = s.query('match', country = country_query)

    if len(loc_query) > 0:
        s = s.query('match', location = loc_query)

    if len(cats_query) > 0:
        s = s.query('match', categories = cats_query)

    # highlight
    s = s.highlight_options(pre_tags = '<mark>', post_tags = '</mark>')
    s = s.highlight('text', fragment_size = 999999999, number_of_fragments = 1)
    s = s.highlight('title', fragment_size = 999999999, number_of_fragments = 1)
    s = s.highlight('starring', fragment_size = 999999999, number_of_fragments = 1)
    s = s.highlight('director', fragment_size = 999999999, number_of_fragments = 1)
    s = s.highlight('language', fragment_size = 999999999, number_of_fragments = 1)
    s = s.highlight('country', fragment_size = 999999999, number_of_fragments = 1)
    s = s.highlight('location', fragment_size = 999999999, number_of_fragments = 1)
    s = s.highlight('categories', fragment_size = 999999999, number_of_fragments = 1)

    # determine the subset of results to display (based on current <page> value)
    start = 0 + (page - 1) * 10
    end = 10 + (page - 1) * 10

    # execute search and return results in specified range.
    response = s[start:end].execute()

    # insert data into response
    resultList = {}
    for hit in response.hits:
        result = {}
        result['score'] = hit.meta.score

        if 'highlight' in hit.meta:
            if 'title' in hit.meta.highlight:
                result['title'] = hit.meta.highlight.title[0]
            else:
                result['title'] = hit.title

            if 'text' in hit.meta.highlight:
                result['text'] = hit.meta.highlight.text[0]
            else:
                result['text'] = hit.text

            if 'starring' in hit.meta.highlight:
                result['starring'] = hit.meta.highlight.starring[0]
            else:
                result['starring'] = hit.starring

            if 'director' in hit.meta.highlight:
                result['director'] = hit.meta.highlight.director[0]
            else:
                result['director'] = hit.director

            if 'language' in hit.meta.highlight:
                result['language'] = hit.meta.highlight.language[0]
            else:
                result['language'] = hit.language

            if 'country' in hit.meta.highlight:
                result['country'] = hit.meta.highlight.country[0]
            else:
                result['country'] = hit.country

            if 'location' in hit.meta.highlight:
                result['location'] = hit.meta.highlight.location[0]
            else:
                result['location'] = hit.location

            if 'categories' in hit.meta.highlight:
                result['categories'] = hit.meta.highlight.categories[0]
            else:
                result['categories'] = hit.categories

        else:
            result['title'] = hit.title
            result['text'] = hit.text
            result['starring'] = hit.starring
            result['director'] = hit.director
            result['language'] = hit.language
            result['country'] = hit.country
            result['location'] = hit.location
            result['categories'] = hit.categories

        resultList[hit.meta.id] = result

    # make the result list available globally
    gresults = resultList

    # get the total number of matching results
    result_num = response.hits.total

    # if we find the results, extract title and text information from doc_data, else do nothing
    if result_num > 0:
        return render_template('page_SERP.html', results = resultList, res_num = result_num, page_num = page,
                               queries = shows, all_matched = all_matched)
    else:
        message = []
        if len(full_text_query) > 0:
            message.append('Unknown search term: ' + full_text_query)
        if len(star_query) > 0:
            message.append('Cannot find star: ' + star_query)
        if len(director_query) > 0:
            message.append('Cannot find director: ' + director_query)
        if len(lan_query) > 0:
            message.append('Cannot find language: ' + lan_query)
        if len(country_query) > 0:
            message.append('Cannot find country: ' + country_query)
        if len(loc_query) > 0:
            message.append('Cannot find location: ' + loc_query)
        if len(cats_query) > 0:
            message.append('Cannot find categories: ' + cats_query)

        return render_template('page_SERP.html', results = message, res_num = result_num, page_num = page,
                               queries = shows)


# display a particular document given a result number
@app.route("/documents/<res>", methods = ['GET'])
def documents(res):
    global gresults
    film = gresults[res]
    filmtitle = film['title']
    for term in film:
        if type(film[term]) is AttrList:
            s = "\n"
            for item in film[term]:
                s += item + ",\n"
            film[term] = s
    # fetch the movie from the elasticsearch index using its id
    movie = Movie.get(id = res, index = index_name)
    filmdic = movie.to_dict()

    # in case of no runtime data
    if 'runtime' in filmdic:
        film['runtime'] = str(filmdic['runtime']) + " min"
    else:
        film['runtime'] = "N/A"

    return render_template('page_targetArticle.html', film = film, title = filmtitle)


if __name__ == "__main__":
    app.run(debug = True)
