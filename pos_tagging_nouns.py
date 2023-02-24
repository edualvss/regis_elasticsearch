import os
import xml.etree.ElementTree as xmlET
import json

import spacy
from elasticsearch import Elasticsearch


def get_xml_files(path):
    files = os.listdir(path)
    print('Number of files: ',len(files))
    files = [path+'/'+f for f in files]
    return files

def get_file_info(file):
    tree = xmlET.parse(file)
    add = tree.getroot()
    doc = add[0]
    fields = doc.findall('field')
    docid = fields[0]
    text = fields[3]
    return docid.text, text.text


def get_nouns(doc, skip, length):
    i = 0
    noun_count = 0
    nouns = []
    for token in doc:
        # Ignore space, punctuation, digits, brackets and quotes
        if token.is_space or token.is_punct or token.is_digit or token.is_bracket or token.is_quote:
            continue
        
        # 'skip' the first tokens
        if i < skip:
            i += 1
            continue

        # Ignore some irrelevant words
        if token.lemma_ == 'palavras-chave' or token.lemma_ == 'palavra-chave' or token.lemma_ == 'Key-words':
            continue

        # Ignore 2 characters tokens
        if len(token.lemma_) < 3:
            continue

        if token.pos_ == 'NOUN':
            word = token.lemma_.lower()
            if word not in nouns:
                nouns.append(word)
                noun_count += 1
#                print(token.lemma_, token.pos_) # Print lemma and POS (part-of-speech) tag
        
        if noun_count == length:
            break
    return nouns

def process_file(text,docid, skip, length):
    doc = nlp(text)
    print(docid, ' have "', len(doc), '" tokens and starts with: ', doc[1])

    nouns = get_nouns(doc,skip,length)
    if len(nouns) < length:
        nouns = get_nouns(doc,0, length)
        if len(nouns) < length * 0.5:
            nouns = get_nouns(doc,0,length*0.2)

#    print(len(nouns),' words: ',nouns) # Print the nouns to be included
    return nouns

def process_collection(documents_path, skip_tokens, amount_nouns):
    files = get_xml_files(documents_path)

    es = Elasticsearch("http://localhost:9200")

    file_count = 1
    total_files = len(files)
    for f in files:
        print('Processing file: ', f, ' - ', file_count, ' of ', total_files)
        file_count += 1
        docid, text = get_file_info(f)
        # Remove special characters (not allowed in json file)
        text = text.replace('\"','')
        text = text.replace('\n',' ')
        text = text.replace('”','')
        text = text.replace('“','')
        text = text.replace('\\','')
        text = text.replace('/', '')
        text = text.replace('\r',' ')
        text = text.replace('\t',' ')
            
        # Spacy characters capacity is 1.000.000 (limitation)
        # Truncate huge files in 100.000 characters
        nouns = []
        if len(text) > 100000:
            nouns = process_file(text[0:100000],docid, skip=skip_tokens, length=amount_nouns)
        else:
            nouns = process_file(text,docid, skip=skip_tokens, length=amount_nouns)

        string_tags = ' '.join(nouns)

        # Update documents in Elasticsearch
        if len(nouns) > 0:
            tags = {"tags": nouns}
            tags = {"tags": string_tags}
#            print(string_tags)
            resp = es.update(index='regis', id=docid, doc=tags)
            print(resp['result'])

        # Index documents in Elasticsearch
#        doc = {
#            "docid": docid,
#            "tags": string_tags,
#            "text": text
#        }
#        resp = es.index(index='regis',id=docid,document=json.dumps(doc))
#        print(resp['result'])

#        break  # Test with just one file


############# Program #############

nlp = spacy.load('pt_core_news_lg') # Large train model
#nlp = spacy.load('pt_core_news_sm') # Short train model
process_collection('./documents', skip_tokens=0, amount_nouns=100) # Without ignore tokens
#process_collection('./documents', 2000, 100) # Ignoring the first 2.000 tokens