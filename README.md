
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

### Workspace

#### Environment
* ElasticSearch 7.17.8 in a Docker Container (for infrastructure);
* Python 3.8.8 (for script and Django app);
* Django Python library 4.1.4 (for search app);
* requests Python library 2.25.1 (for request/query ES from search app);
* xml.etree Python library; and (for read regis collection in XML)
* json Python library (for adapt to ES format)

Resource used to dev: Macbook Pro M1 - 8GB RAM - OS X Ventura 13.0.1.

#### ElasticSearch
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

#### Adapter Script
