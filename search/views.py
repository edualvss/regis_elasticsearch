from django.shortcuts import render
from . import models
#from django.http import HttpResponse
#from django.template import loader

# Create your views here.

hits = []

def index(request):
    query_results = None
    get_params = request.GET

    if 'q' in get_params:
#        print(get_params['q'])
        query_results = models.processar_consulta(get_params['q'])
        if query_results['status'] != 200: # Falha
            query_results = None
        else:
            hits = query_results['hits']
            #print(hits)

    context = {
        'query_results': query_results
    }
    return render(request,'search/index.html',context)