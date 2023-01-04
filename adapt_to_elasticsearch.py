import os
import xml.etree.ElementTree as xmlET
import json

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
                "k": 20,
                "normalize": True
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
                "query": {"match": {"text": title} },
                "ratings":[]
            }
        }

        # For each document in 'qrels.txt' with the specific query_num
        for doc in qrels[query_num]:
            evaluated_doc = {"_index": "regis", "_id":doc['docid'],"rating":doc['rating']}
            request['request']['ratings'].append(evaluated_doc)
        rank_eval_obj['requests'].append(request)

    return rank_eval_obj


#### Main
option = int(input("Choose an action:\n1) Ingest REGIS file in Elastic Search (ES)\n2) Convert XML files to JSON\n3) Generate ES JSON for rank evaluation\n"))

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
else:
    print("Invalid option...exiting")