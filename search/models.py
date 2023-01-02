from django.db import models

import requests

# Create your models here.


es_url = 'http://localhost:9200/regis'

def processar_consulta(query):
#    api_url = es_url+'/_search?_source=false'
#    api_url = es_url+'/_search'
    api_url = es_url+'/_search?pretty'
    query_obj = {
        "query" : { 
            "match" : { 
                "text" :  query
            }
        } 
    }
#    print(query_obj)
    response = requests.get(api_url,json=query_obj)
    json_result = response.json()
    
    hits = json_result['hits']['hits']
    hits = ajustar_parametros(hits)

    response_obj = {
        "took": json_result['took'],
        "total": json_result['hits']['total']['value'],
        "max_score":json_result['hits']['max_score'],
        "hits": hits,
        "status" : response.status_code
    }

#    print(response.headers["Content-Type"])
    return response_obj

def ajustar_parametros(encontrados):
    for doc in encontrados:
        doc["source"] = doc["_source"]
        doc["score"] = doc["_score"]
        del doc["_source"]
        del doc["_score"]
    return encontrados