from Bio import Entrez

from tools import pmc2pubmed


def search(query, qty=5):
    Entrez.email = "email"
    handle = Entrez.esearch(db='pmc',
                            sort='relevance',
                            retmax=str(qty),
                            retmode='xml',
                            term=query)
    results = Entrez.read(handle)

    ids = pmc2pubmed(results['IdList']) if int(results["Count"]) > 0 else []
    return ids


# Not used for now
def query_correction(query):
    Entrez.email = "email"
    handle = Entrez.espell(term=query)
    record = Entrez.read(handle)
    if record["CorrectedQuery"] != "":
        return record['CorrectedQuery']
    else:
        return ""


def fetch_details(id_list):
    """
        - Return article summaries in json format
        - Return error if any occurs
        """
    try:
        ids = ','.join(id_list)
        Entrez.email = "email"
        handle = Entrez.efetch(db='pubmed',
                               retmode='xml',
                               rettype='full',
                               id=ids)
        results = Entrez.read(handle, validate=False)
        return results

    except Exception as e:
        return {"fetch_details": str(e)}
