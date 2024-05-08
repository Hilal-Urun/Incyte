import re
import traceback
from datetime import datetime

from Bio import Entrez
from Bio.Entrez.Parser import StringElement


def pmc2pubmed(id_list):
    pubmed_ids = []
    ids = ','.join(id_list)
    Entrez.email = "email"
    handle = Entrez.elink(dbfrom="pmc", db="pubmed", linkname="pmc_pubmed", id=ids, retmode="text")
    result = Entrez.read(handle)
    for i in result[0]['LinkSetDb'][0]['Link']:
        pubmed_ids.append(i['Id'])
    handle.close()
    return pubmed_ids


def destructure_paper_summary(paper):
    """
    Instead of initialize Article object with the json
    I will initialize it giving different parameters
    In order to favor generalization and re-use of the init method
    """
    # Retrieving Title
    final_obj = {'Title': re.sub('<.*?>', "", paper['MedlineCitation']['Article']['ArticleTitle'])}
    # Retrieving keywords
    keywords = []
    if 'KeywordList' in list(paper['MedlineCitation'].keys()) and len(
            paper['MedlineCitation']['KeywordList']) > 0:
        for keyword in paper['MedlineCitation']['KeywordList'][0]:
            keywords.append(str(keyword))

    # Retrieving authors
    authors = []
    try:
        for author in paper['MedlineCitation']['Article']['AuthorList']:
            if 'ForeName' in author and 'LastName' in author:
                authors.append(author['ForeName'] + " " + author['LastName'])
    except KeyError:
        authors.append('Unfortunately, no authors were found')

    final_obj['authors'] = authors
    final_obj['pubdate'] = paper['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate']
    for key in final_obj['pubdate']:
        if type(final_obj['pubdate'][key]) is StringElement:
            final_obj['pubdate'][key] = str(final_obj['pubdate'][key])
    abstact_text = ""
    # Retrieving abstract
    abstract = {'text': ''}
    if 'Abstract' in paper['MedlineCitation']['Article'].keys():
        for paragraph in paper['MedlineCitation']['Article']['Abstract']['AbstractText']:
            abstract['text'] += paragraph
            abstact_text += paragraph
    final_obj['abstract'] = re.sub(r"<.*?>", "", abstract['text'])

    pmc_id = ''
    for potential_pmc_id in paper['PubmedData']['ArticleIdList']:
        if potential_pmc_id.startswith('PMC'):
            pmc_id = str(potential_pmc_id)

    final_obj['pmc_id'] = pmc_id
    final_obj['keywords'] = keywords
    return final_obj


def remove_special_characters(text):
    t = ""
    for i in text:
        # Store only valid characters
        if ('A' <= i <= 'Z') or ('a' <= i <= 'z') or " ":
            t += i
    return t


def pubdate_field_extraction(obj, field_name):
    try:
        if field_name in obj:
            field = field_name
        elif field_name.capitalize() in obj:
            field = field_name.capitalize()
        else:
            return None

        if obj[field] is None or obj[field] == '':
            return None

        if type(obj[field]) is int:
            return obj[field]

        if type(obj[field]) is str and obj[field].isnumeric():
            return int(obj[field])

        if field_name == 'month':
            if len(obj[field]) == 3:
                return datetime.strptime(obj[field], '%b').month
            else:
                return datetime.strptime(obj[field], '%B').month

        return None
    except:
        traceback.print_exc()
        return None


def pubdate_deconstruct(obj):
    if obj is None:
        return None

    return {'year': pubdate_field_extraction(obj, 'year'),
            'month': pubdate_field_extraction(obj, 'month'),
            'day': pubdate_field_extraction(obj, 'day')}
