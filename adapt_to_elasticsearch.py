import os
import xml.etree.ElementTree as xmlET
import json
import math
import csv

from elasticsearch import Elasticsearch


# Parse XML documents of regis collection to JSON and return as string.
# The second return data is the 'docid' as string
def xml_to_json(xml_filename):
    # XML Parser
    tree = xmlET.parse(xml_filename)
    # First/root tag 
    add = tree.getroot() # tag <add>
    # Only child tag
    doc = add[0]         # tag <doc> 

    # Internal fields in doc
    fields = doc.findall('field') # childs of <doc>
    docid = fields[0]
    filename = fields[1]
    filetype = fields[2]
    text = fields[3]

    json_content = """
        "docid":"{}",
        "filename":"{}",
        "filetype":"{}",
        "text":"{}"
    """
    # Remove special characters (not allowed in json file)
    text = text.text.replace('\"','')
    text = text.replace('\n',' ')
    text = text.replace('”','')
    text = text.replace('“','')
    text = text.replace('\\','')
    text = text.replace('/', '')
    text = text.replace('\r',' ')
    text = text.replace('\t',' ')

    json_content = '{\n'+json_content.format(docid.text,filename.text,filetype.text,text)+'\n}'
#    json_content = json_content.format(docid.text,filename.text,filetype.text,text.text)
    return json_content, docid.text



############# Ingestion section

def get_xml_files(path):
    files = os.listdir(path)
    print('Number of files: ',len(files))
    files = [path+'/'+f for f in files]
    return files


def ingest_files():
    es = Elasticsearch("http://localhost:9200/")
    files = get_xml_files('./documents')
    for f in files:
        print('Ingesting file: ',f)
        doc, docid = xml_to_json(f)

        resp = es.index(index='regis',id=docid,document=doc)
        print(resp['result'])
#        break # Use break to ingest just the first file - test purpose


############# XML to JSON conversion section

def convert_xml_regis_files_to_json(srcpath,destpath):
    files = get_xml_files(srcpath)  # Get all xml files from 'srcpath'

    if not os.path.exists(destpath):
        os.mkdir(destpath)

    for f in files:
        filename = f[f.rfind('/'):len(f)-4] # Remove the path and keep only the filename
        print('Saving...',filename)
        json_content = xml_to_json(f)
        save_filename = destpath + filename + '.json'
        with open(save_filename,'w') as outfile:
            outfile.write(json_content)
#        break # Use break to save just the first file - test purpose


############# Generate JSON for REGIS collection Rank Evaluation in Elastic Search

# Return a dict with such format:
# {
#   "Q1":[{"docid":"BR-BG.XXXXX","rating":1},{"docid":"BR-TY.XXXXX","rating":2},...],
#   "Q2":[{"docid":"BR-BT.XXXXX","rating":2},{"docid":"BR-TX.XXXXX","rating":0},...],
#    ...
# }
def read_qrels_file(filename):
    qrels = dict()

    with open(filename,'r') as f:
        for line in f:
            fields = line.split()
            query_id = fields[0]
            doc_id = fields[2]
            rating = int(fields[3])

            if query_id not in qrels:
                qrels[query_id] = []

            doc_evaluated = {
                "docid": doc_id,
                "rating": rating
            }
            qrels[query_id].append(doc_evaluated)
        f.close()
    return qrels

def generate_regis_rank_eval_obj():
    queries_tree = xmlET.parse('queries.xml')
    root_tag = queries_tree.getroot()

    qrels = read_qrels_file('qrels.txt')

    rank_eval_obj = {
        "requests":[],
        "metric": {
            "dcg" : {
                "k": 20,            # Number of documents retrieved
                "normalize": True   # True: Use NDCG, False: Use only DCG
            }
        }
    }

    # For each query in 'queries.xml'
    for top in root_tag:
        query_num = top[0].text
        title = top[1].text
##        desc = top[2].text # Unused field
##        narr = top[3].text # Unused field

        request = {
            "id": query_num,
            "request": {
                "query": {"match": {"text": title} }
            },
            "ratings":[]
        }

        # For each document in 'qrels.txt' with the specific query_num
        for doc in qrels[query_num]:
            evaluated_doc = {"_index": "regis", "_id":doc['docid'],"rating":doc['rating']}
            request['ratings'].append(evaluated_doc)
        rank_eval_obj['requests'].append(request)

    return rank_eval_obj


############## Calculate DCG of REGIS Collection

def calculate_dcg(gain, pos):
    return gain / math.log2(1+pos)  # DCG is accumulated of 'rating_doc[i] / log2(i + 1)'

def calculate_dcg_alternative(gain,pos): # This is the formula used in Elasticsearch
    return (math.pow(2,gain)-1) / math.log2(1+pos) # DCG is accumulated of '2 ** rating_doc[i] - 1 / log2(i + 1)'

def generate_regis_metrics_on_evaluated_docs(discount_formula):
    obj = {}
    qrels = read_qrels_file('qrels.txt')

    for key,value in qrels.items():
        obj[key] = {'g': [], 'cg': [], 'dcg': []}
        cg = 0
        dcg = 0
        pos = 1
        for doc in value:
            gain = doc['rating']
            cg = cg + gain
#            dcg = dcg + calculate_dcg(gain,pos)
#            dcg = dcg + calculate_dcg_alternative(gain,pos)
            dcg = dcg + discount_formula(gain,pos)
            obj[key]['g'].append(gain)
            obj[key]['cg'].append(cg)
            obj[key]['dcg'].append(dcg)
            pos += 1
        obj[key]['n'] = pos - 1

    return obj

def generate_regis_idcg(metrics, top_k, discount_formula):
    obj = {}
    for key,value in metrics.items():
        value['g'].sort(reverse=True)
        value['idcg'] = []
        idcg = 0
        pos = 1
        for gain in value['g']:
#            indcg += calculate_dcg(gain,pos)
#            indcg += calculate_dcg_alternative(gain,pos)
            idcg += discount_formula(gain,pos)
            value['idcg'].append(idcg)
            pos += 1
            if pos == top_k+1:
                break
        obj[key] = {"idcg": idcg, "k": pos-1}

    return obj


############################ Elasticsearch Rank Evaluation 

def read_es_rank_eval_result(filename):
    rank_obj = None
    with open(filename,'r') as f:
        rank_obj = json.load(f)
    return rank_obj

def process_rank_evaluation(rank_obj, metrics, discount_formula):
#    print(rank_obj['details']['Q1'])
#    print(metrics)

    with open('rank_eval_detail.csv',mode='w') as rank_file:
        header = ['QUERY','#','DOCID', 'SCORE', 'G', 'CG','DCG','IDCG','NDCG']
        writer = csv.DictWriter(rank_file, fieldnames=header)
        writer.writeheader()

        for query in rank_obj['details']:
            obj = rank_obj['details'][query]
            i = 1
            cg = 0
            dcg = 0
            for doc in obj['hits']:
                idcg = metrics[query]['idcg'][i-1]
                rating = doc['rating']
                if rating != None:
                    cg += rating
                    dcg += discount_formula(rating,i)
                ndcg = dcg / idcg
                writer.writerow({'QUERY':query,'#': i, 'DOCID': doc['hit']['_id'],'SCORE':doc['hit']['_score'],'G': rating, 'CG': cg, 'DCG':dcg, 'IDCG': idcg, 'NDCG': ndcg})
                i+=1


#### Main
option = int(input("""
Choose an action:
\n1) Ingest REGIS collection in Elastic Search (ES)
\n2) Convert Regis XML documents to JSON
\n3) Generate JSON for Elastic Search rank evaluation
\n4) Calculate the CG, DCG, IDCG of REGIS evaluated documents (generates a CSV file)
\n"""))


if option == 1:
    ingest = input("Do you want ingest files (s/n)?\nIt will take a long time (copying ~3.3GB)")
    if ingest == 's' or ingest == 'S':
        print('This script must be in the REGIS collection root path (with "documents" directory in the same level)')
        print('The index name defined to ingest documents is "regis" in ElasticSearch')
        print('Please wait...')
        ingest_files()
    else:
        print("Ingestion aborted")
elif option == 2:
    print('This script must be in the REGIS collection root path (with "documents" directory in the same level)')
    convert_xml_regis_files_to_json('./documents','./json')
elif option == 3:
    print('This script must be in the REGIS collection root path (with "queries.xml" and "qrels.txt" in the same level)')
    rank_eval = generate_regis_rank_eval_obj()
    with open("rank_eval.json",'w',) as outfile:
        json.dump(rank_eval,outfile,ensure_ascii=False,indent=2)
elif option == 4:
    top_k = 10
#    formula = calculate_dcg
    formula = calculate_dcg_alternative
    
    # From collection
    metrics = generate_regis_metrics_on_evaluated_docs(formula)
    idcg = generate_regis_idcg(metrics, top_k, formula)
#    print(metrics)
#    print(idcg)
 
    # From Elasticsearch index / rank_eval API result
    rank_eval_result_file = "rank_eval_all_queries_response-top10.json"
    rank_obj = read_es_rank_eval_result(rank_eval_result_file)
#    print(rank_obj)
    process_rank_evaluation(rank_obj, metrics, formula)
    
else:
    print("Invalid option...exiting")
