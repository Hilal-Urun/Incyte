# WARNING: THIS IS OUTDATED

# INSTALLATION & RUN

### Using docker 
To run the local developement ```docker-compose up ```, if you want to rebuild after some changes just excute ```docker-compose up --build```, 

For running the deployement images : ```docker-compose -f docker-compose-deploy.yml up```, In the same manner for reconstructing the container use the ```--build``` flag. 

### Without Docker
  - locally: `python mid_level.py`
  - prod: `gunicorn --workers 5 --preload --bind 127.0.0.1:8000 --timeout 600 --worker-class=uvicorn.workers.UvicornWorker mid_level:mid`  
`gunicorn` allows the `--preload` flag, which loads the model into memory before the workers are spawned. This is important because the model is large and takes a long time to load.  
`--timeout` is set to 600 seconds (10 minutes) for this dev environment. In production, this should be set to a lower value, such as 30 seconds.
  - Same thing goes for `top_level.py`.  

# Install search engine as a library. 
```pip install -e . ``` , or ```install.sh ```

if you experience some errors (AttributeError: module 'collections' has no attribute 'MutableMapping') This means that your default python version is set up to 2.x
, please follow this instructions. 

```sudo update-alternatives --config python3 ``` and select a python3-version<=3.9,>3.6 (preferably 3.8)
```pip install -U pip setuptools wheel &&  pip --version pip && pip install -e . ```

### Through Django
 ```cd app && python manage.py runserver``` 


# Quick tour


---methods.py


There are two class inside the script. Search class is the parent class and the pdf class is the child class of it.

--Search class has 10 methods;

-correction() && isCorrection() handle spelling and grammer checking issues and return corrected query

-search() returns list of pubmed articles id's most related to the query

-fetch_details(id_list) returns details of the articles such as published date, title, authors and abstracts

-dict_query(papers,id_list) returns a dictionary version of fetched details

-abstract_analyses(dict_data) analyses relevance between query and abstract and gives an accuracy score for each

-ordering_new(dict_data) according to the accuracy scores calculated with abstract_analyses method, sorts articles

-one_title_printing(ordered_dict_data) prints most related article 

-title_printing(ordered_dict_data) prints all sub-data of articles

-summaryInfo(id_list) pipeline of above methods and return ordered dictionary data

--Pdf class is a child class of Search class and contains 7 methods

-pubmed2pmc(id_list) returns converted versions of pubmed ids to pmc ids

-keyword_extraction(all_text) if article has no keywords, it extracts keywords from article and returns it

-abstract_extraction(data) extracts abstract part from the metadata

-text_dict(pmc_id) returns a dictionary contains metadata of the pdf

-paragraph_query_sim(paragraph) returns an accuracy score for relevance between each paragraph and query 

-abstract_score(abstarct) returns an accuracy score for relevance between each abstract and query

-article_printing(article_dict) prints formatted metadata to the screen



---search-pipeline.py

-child process() creates an instance of the pdf and returns it

-query_search(json_query) takes a query as json obj and returns possible articles pubmed ids and created child process

-abstracts(ids, child) returns summary information of the articles and id of choosen article from user

-meta_data(choosen_id, child) returns choosen article's metadata as json obj
 

# Documentation: Incyte-Data-Science

The aim of the project is the development of an efficient tool for the research of scientific papers through a query. The tool needs to fetch papers from different databases and arrange them so that the order in which they are suggested to the user, respects the contextual matching of the query. Furthermore, the same procedure can be leveraged to suggest connected articles from a chosen paper and to lead the user to the searched piece of information inside the text of the paper itself. The project is conceptually divided into 3 branches:

-NATURAL LANGUAGE PROCESSING : The abstracts and texts of the papers need to be analyzed with an NLP pipeline so that is possible to extract from them the required information to connect them to the initial query.

-CRAWLERS : The user is eventually going to choose one of the papers suggested for further investigation. The chosen paper will be downloaded from the database of origin so that is possible for the tool to analyze its text and suggest the user where to look for.

-PDFtoTEXT MECHANISM : The papers are normally in a PDF format. Consequently, to extract text from them, it’s necessary a tool that can elaborate the pdf page into an ordered structure of branches, based on the paragraphs.

BACKGROUND:

The idea of the whole project is that when a user search for scientific papers on a search engine, the matching of those papers or articles is made through a series of Boolean condition regarding the keywords used. This method relies on the presupposition that the keywords used for the article can represent to an efficient degree, the informative content of the paper itself.

This presupposition may seem trivial, but it defines the search for a paper into a linguistical match. Specifically for scientific papers, this isn’t enough.

A more contextual matching is needed, that relies on the ability of the analysis to generate an evaluation of similarity with respect to the query.
Therefore, the project has the goal of developing a scoring method for abstracts and texts based on the assessment of similarity between them and the proposed query.

APIs:

In this project 2 different APIs are used:

1.EXPERT.AI : Expert.ai is a pre-trained platform for NLP; inside the project is used for the linguistic and contextual analysis. Starting from a text. It allows to extract main lemmas, main sentences, main phrases, main topics and main syncons (linguistical token with a contextual classification); for each one of these elements a score is associated. This score is based on a relevance assessment of the element in the analyzed text (For specific information regarding the relevance score, it’s possible to read the Expert.ai documentation here: https://docs.expert.ai/nlapi/latest).


2.BIOENTREZ : BioEntrez is the Python library for the extraction of information regarding scientific papers on PubMed.

 
METHODS:

Here is the logistic structure and data organization used for the tool, divided into step.

1.PAPERS SEARCH:

1.1.QUERY INITIALIZATION: The user inserts the query. ✅

1.2.QUERY CORRECTION: After user inserts the query spelling and grammatical mistakes should be corrected. ✅

1.3.ASKED QUERY IS CORRECT: After corrected query and fetching information, beginning of the results, return a text as are you looking for this? ✅

1.4.QUERY ANALYSIS: The query is analyzed through the Expert.ai and a dictionary is created with all the relevant information for the matching process. The dictionary is called relevant_matching_info. ✅

1.5.	FETCHING PROCESS: From the query, a list of 20 papers from Pubmed is extracted through the BioEntrez library. The ‘best_match’ parameter is used. From this step a dictionary is generated, which contains as items the papers with the related pieces of information (title, id, abstract, references, authors, etc.). Each of these items has, as key, the title of the paper. ✅

1.6.	ABSTRACT ANALYSIS: The abstract of every fetched paper is analyzed through Expert.ai, extracting all the relevant information. ✅

1.7.	SCORING PROCESS: Confronting the two previously generated dictionaries, a score is associated to every paper which is the sum of the relevance scores of every shared element between the text of the abstract and the query. ✅

1.8.	MEAN SCORE: A final score is generated which is the average between the ‘contextual’ score and the score associated with the fetching position (rescaled between 0-100). ✅

1.9.	TITLE PRINTING: The papers are presented ordered by the final mean score associated with the paper. ✅

1.10.	ANALYSING PAPERS CONTENT: When the primal operations continue, in the background papers will analyzed and according to their analysis, information got will stored in the (temporary or not) database for future and more correct keywords ✅


2.	CONNECTED ARTICLES:

2.1.	ARTICLE FETCHING FROM A TITLE: Starting from the title of a paper and the dictionary of the relevant matching information for the query, it’s possible to extract 10 articles correlated to the first one. ✅

2.2.	IF ABSTRACT IS EMTY: If abstract is empty, what should we do ? When we extract the article, we don’t have all the text data and when reviewed the api I couldn’t find any function for that ❓

2.3.	SCORING METHOD (e.g. 1.4, 1.5, 1.6): Starting from the papers, the same process of scoring previously described is applied. A dictionary is generated which has, as keys, the title of the papers, and as values, the relevant pieces of information extracted from every paper and the final score. ✅

2.4.	TITLE PRINTING: The papers are presented ordered by the final mean score associated with the paper. ✅

2.5.	BYPRODUCTS: During the BioEntrez call, two files are generated in order to create the connection with the database necessary for the extraction of the connected articles (elink.dtd, efetch.dtd) ❓


3.	TEXT EVALUATION:

3.1.	TEXT DICTIONARY: From the PDF file of the paper, a dictionary is produced. Inside this dictionary it’s possible to find as items the text of the paragraphs of paper. Each of these items has a key, which is the title of the corresponding paragraph. ✅

3.2.	SCORING PROCESS (e.g. 1.5,1.6): Starting from the dictionary of the text and the dictionary of the relevant matching information of the query, the previously contextual scoring method is applied. ✅

3.3.	SCORING WİTH HUGGING FACE: Should we score the abstract relevance to the query, because it gives almost the same results with scoring function used now. And should we apply question answering on all text? ✅

3.4.	HUGGING FACE FOR FINDING MOST RELATED PARAGRAPH: For each article, according to their relevance with the query they are scored and when user select the article can see the most related part or parts ✅

3.5.	KEYWORD EXTRACTION: Some of articles don’t have keywords, find keywords of the article and add the dictionary. ✅

3.6.	Q&A PIPELINE ACCURACY SCORE: For each of the paragraph’s text a new score is generated which is the accuracy value of a question and answer NLP pipeline, pretrained and downloaded from Hugging Face (https://huggingface.co/deepset/roberta-base-squad2). The accuracy extracted is referred to the ability of the text to answer the hypothetical question given by the query. The accuracy value is rescaled between 0-100. ✅

3.7.		MEAN SCORE: A final score is generated which is the average between the ‘contextual’ score and the score of the Q&A pipeline. ✅

3.8.	INDEX PRINTING: The index of the paragraphs’ title is then presented to the user ordered by the final averaged score. ✅

3.9.	Parallel computing and Kubernetes part !! ❓

3.10	Search pipeline :  Search query -> Articles (analysed background) -> just show one of article abstract etc and ask "Are you looking for it?"
if answer is yes show the other articles information else search until user answer is yes -> After user click an article fetch the meta data from db with also showing acc of the relevance between paragraphs and query. ❓

3.11	Next if user has an account save the metadeta s(he) wants on the profile. ❓


4.	MONGODB

4.1.	Saving meta data ✅

4.2 	When a query searched find id's and skip them which are already fetched and analysed.


	

APPLICATION:

The designed experience for the users of the tool would be the following:

•	The user enters the query into the search engine

•	A list of papers is presented to the user

•	The user navigates through the papers proposed

•	The user chooses one of the papers for further investigation

•	A list of connected papers is presented to the user

•	The user is guided into the text of the paper to find where the searched information is.

NEXT STEPS:

The elements of the pipeline described in the documents are the one currently implemented. The future steps towards the final development of the whole projects are:

•	Extension of the fetching mechanism to other databases internal (Incyte’s private DB) and external (Google Scholar).

•	Development of the crawler to download the papers from different websites.

•	Development of a comprehensive PDFtoTEXT tool that can be applied to a plethora of different layout structures

•	Development of a tool for misspellings checks. Possible solution: PySpellChecker offers the possibility to specifically train the checks of the spelling with dictionaries, list or texts of required words.
