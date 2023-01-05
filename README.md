
# regis_elasticsearch - Eduardo Alves da Silva - IR UFAM
## Web Search application with ElasticSearch for REGIS Collection

### About REGIS Collection
The REGIS Collection is available in: [regis-collection repository](https://github.com/Petroles/regis-collection).

REGIS is a public repository for the paper **REGIS: A Test Collection for Geoscientific Documents in Portuguese** 

**REF:** *Lucas Lima de Oliveira, Regis Kruel Romeu, Viviane Pereira Moreira. "REGIS: A Test Collection for Geoscientific Documents in Portuguese". ACM SIGIR Forum, Association for Computing Machinery, 2021. DOI:[10.1145/3404835.3463256](https://dl.acm.org/doi/10.1145/3404835.3463256)*

## This code is result of the Information Retrieval class work in UFAM/IComp/PPGI with the REGIS Collection and ElasticSearch
### Developed tools:
1. A Python script to adapt the REGIS Collection information to ElasticSearch (ES) format; and
2. Web Search app to query some information in REGIS Collection indexed with Elastic Search.

## Workspace


### Environment
* ElasticSearch 7.17.8 in a Docker Container (for infrastructure);
* Python 3.8.8 (for script and Django app);
* Django Python library 4.1.4 (for search app);
* requests Python library 2.25.1 (for request/query ES from search app);
* xml.etree Python library; and (for read regis collection in XML)
* json Python library (for adapt to ES format)

Resource used to dev: Macbook Pro M1 - 8GB RAM - OS X Ventura 13.0.1.



### ElasticSearch
Docker container from 7.17.8 image (without security policy in ES).

**Pull the image:**

`docker pull docker.elastic.co/elasticsearch/elasticsearch:7.17.8-arm64`

*OBS: arm64 architecture of M1 chip. The conventional uses x86, just remove "-arm64" in the end.*

**Create a "elastic" network:**

`docker network create elastic`

**Create and run a container instance named es01 in ES single-mode on 9200 and 9300 ports:**

`docker run --name es01 --net elastic -p 127.0.0.1:9200:9200 -p 127.0.0.1:9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.17.8-arm64`

**Create the "regis" index in ES with a specific mapping to the regis collection fields (via curl in terminal):**

` curl -X PUT "localhost:9200/regis?pretty" -H 'Content-Type: application/json' -d'
{
	"mappings": {
		"properties":{
			"docid": {"type":"text"},
			"filename" : {"type":"text"},
			"filetype" : {"type":"keyword"},
			"text": {"type":"text"}
		}
	}
}
'
`

*The mapping is:*
 ```
{
	"mappings": {
		"properties":{ 
			"docid": {"type":"text"},
			"filename" : {"type":"text"},
			"filetype" : {"type":"keyword"},
			"text": {"type":"text"} 
		}
	}
}
```

For ingest files on 'regis' index created, the python script below was used.



### Adapter Script

The adapter script [`adapt_to_elasticsearch.py`](https://github.com/edualvss/regis_elasticsearch/blob/main/adapt_to_elasticsearch.py) contains:

1. A function to **convert** the Regis XML documents (inside *documents* folder) in a JSON string format compliant with ElasticSearch.
2. A procedure to **ingest** the Regis documents in ElasticSearch index 'regis' (elasticsearch docker container need to be up).
3. A procedure to **convert and save** Regis XML documents in a JSON string format compliant with ES in files (a **json** folder will be created).
4. A function to **create and return a dict** with the regis evaluated queries (file: qrels.txt of Regis Collection). Each evaluated query id (eg. Q1, Q2, Q3,...) become an "object" that have the 'multiple' *docid* and *rating* of the qrels file.
5. A function to **create and return** an object formatted to use in [ElasticSearch ranking evaluation API](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-rank-eval.html). This function read the 'queries.xml' and 'qrels.txt' files of Regis Collection to create the object.
6. A terminal-based menu to the user choose: 1. Ingest documents in ElasticSearch; (2) Convert and save the Regis XML documents in JSON files; (3) Create a JSON file with the ES Ranking Evaluation format for all the evaluated queries in Regis Collection.

*OBS: the script must be on the Regis Collection root path (same level as 'queries.xml', 'qrels.txt' and 'documents' folder)*
