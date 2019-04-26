import re
from elasticsearch_dsl import Search
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q

# s = '"ddd xx" rrr "ttt yyy"'
# pattern = re.compile(r'(?:\B\")(.*?)(?:\b\")')
# r = pattern.sub('', s)
# t = pattern.findall(s)
# while len(t) > 0:
#     print(t.pop())
# print(t)

client = Elasticsearch()
s = Search(using = client, index = "sample_film_index")
q = Q()
q &= Q('multi_match', query = 'd', type = 'cross_fields', fields = ['title', 'text'], operator = 'or')

q |= Q('multi_match', query = 'indian film', type = 'phrase_prefix', fields = ['title', 'text'])

print(q.to_dict())
s = s.query(q)
r = s.execute()
print(r)
