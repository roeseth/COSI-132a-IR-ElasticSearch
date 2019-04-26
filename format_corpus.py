import json
import time
import re

# A script for pre-processing the corpus
start_time = time.time()

with open('films_corpus.json', 'r', encoding = 'utf-8') as data_file:
    # load movies from json file into dictionary
    movies = json.load(data_file)
    data_file.close()

# for each movie entry, fix the "[]" string in empty fields and change it to an empty list
# also, extract the number from string in field 'Time' using Regex
for id in movies:
    if movies[id]["Running Time"] == "[]":
        movies[id]["Running Time"] = []

    if "[]" in movies[id]["Director"]:
        movies[id]["Director"].remove("[]")

    if "[]" in movies[id]["Starring"]:
        movies[id]["Starring"].remove("[]")

    if movies[id]["Country"] == "[]":
        movies[id]["Country"] = []

    if "[]" in movies[id]["Country"]:
        movies[id]["Country"].remove("[]")

    if movies[id]["Language"] == "[]":
        movies[id]["Language"] = []

    if "[]" in movies[id]["Language"]:
        movies[id]["Language"].remove("[]")

    for i, s in enumerate(movies[id]["Time"]):
        # if have 3 or 4-digit time in 'Time', extract and convert to int
        # otherwise, remove it
        if isinstance(s, str) and re.search(r'\d{3,4}', s):
            movies[id]["Time"][i] = int(re.search(r'\d{3,4}', s).group())
        elif not isinstance(s, int):
            movies[id]["Time"].pop(i)

    # remove Running time that does not have a time in it
    if not isinstance(movies[id]["Running Time"], int):
        if isinstance(movies[id]["Running Time"], str):
            s = movies[id]["Running Time"]
            if re.search(r'\d+', s):
                movies[id]["Running Time"] = int(re.search(r'\d+', s).group())
            else:
                movies[id]["Running Time"] = []
        else:
            for i, s in enumerate(movies[id]["Running Time"]):
                if isinstance(s, str) and re.search(r'\d+', s):
                    movies[id]["Time"][i] = int(re.search(r'\d+', s).group())
                elif not isinstance(s, int):
                    movies[id]["Time"].pop(i)

# write-out the formatted corpus
with open('films_corpus.json', 'w', encoding = 'utf-8') as f:
    json.dump(movies, f, indent = 4)

print("=== Format corpus in %s seconds ===" % (time.time() - start_time))
