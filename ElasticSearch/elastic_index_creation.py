import elasticsearch
from sys import argv

def index_creation(indexname,mappingtype):
    #by default this function only create an index locally

    es=elasticsearch.Elasticsearch(['localhost'],port=9200)
    request_body = {
        "settings": {
            "number_of_shards": 5,
            "number_of_replicas": 1
        },

        'mappings': {
            'review': {
                'properties': {
                    'url': {'type': 'text'},
                    'title': {'type': 'text'},
                    'address': {'type': 'text'},
                    'location': {'type': 'geo_point'},
                    'zipcode': {'type': 'text'},
                    'city': {'type': 'text'},
                    'numberofrooms': {'type': 'integer'},
                    'stars': {'type': 'text'},
                    'service': {'type': 'text'},
                    'maxprice': {'type': 'integer'},
                    'minprice': {'type': 'integer'},
                    "insert_date": {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}

            }
            }}
    }
    response=es.indices.create(index='tripadvisor',ignore=400, body=request_body)
    return response

if __name__ == '__main__':
    index_name=argv[1]
    mapping_type=argv[2]
    index_creation(indexname=index_name,mappingtype=mapping_type)
