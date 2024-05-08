import logging
import os
import traceback
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
import uvicorn
from dotenv import load_dotenv
from expertai.nlapi.common.authentication import ExpertAiAuth
from fastapi import FastAPI, Response, Depends
from requests_html import HTMLSession
from starlette.middleware.sessions import SessionMiddleware

from Classes.Exceptions import PDFException
from loguru import logger

load_dotenv()

from env_check import check_required_env_vars, check_optional_env_vars

check_required_env_vars()
check_optional_env_vars()
from indexing.meilisearch import MeilisearchClient

from DBController import db_controller
from caching import cache
from Classes.Article import IncyteArticle, PMCArticle
from Classes.FullArticle import FullPMCArticle, FullArticle, FullIncyteArticle
from Classes.ArticlesList import ArticlesList
from entrez_wrapper import search, fetch_details

from routers.auth.auth import router as auth_router
from routers.auth.auth import get_user_data

logging.basicConfig(level=logging.DEBUG)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("API_SESSION_SECRET_KEY") if os.getenv("API_SESSION_SECRET_KEY") else "change_me")
meilisearch_client = MeilisearchClient()


def get_pmc_articles(query: str, qty: int = 20) -> list[PMCArticle]:
    ids = search(query, qty=qty)
    articles = fetch_details(ids)
    if "PubmedArticle" not in articles:
        return []
    articles = articles['PubmedArticle']
    if len(articles) == 0:
        return []

    with ThreadPoolExecutor(max_workers=len(articles)) as pool:
        articles = list(pool.map(PMCArticle, articles, repeat(query, len(articles))))
        pool.shutdown(wait=True)
    return articles


def get_incyte_articles(query: str, qty: int = 20) -> list[IncyteArticle]:
    ids = meilisearch_client.search_ids(query, limit=qty)
    articles = db_controller.id_search(ids)
    if len(articles) == 0:
        return []

    with ThreadPoolExecutor(max_workers=len(articles)) as pool:
        articles = list(pool.map(IncyteArticle, articles, repeat(query, len(articles))))
        pool.shutdown(wait=True)
    return articles


@app.get('/search', status_code=200)
def search_endpoint(query: str, response: Response, qty: int = 20, filter: int = 3, user=Depends(get_user_data)):
    if not user:
        response.status_code = 401
        return {'error': 'Unauthorized'}
    try:
        ExpertAiAuth().fetch_token_value()
        futures = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            if filter & 1:
                futures.append(pool.submit(get_pmc_articles, query))
            if filter & 2:
                futures.append(pool.submit(get_incyte_articles, query))
            pool.shutdown(wait=True)

        articles: ArticlesList = ArticlesList([])
        for future in futures:
            articles.extend(future.result(timeout=20) or [])

        if len(articles) == 0:
            return []

        articles.db_save()
        articles.rank(query)
        return articles[:qty]
    except Exception:
        traceback.print_exc()
        response.status_code = 500
        return


def article_cleanup(article):
    article['id'] = article.pop('_id')
    return article


@app.get('/home', status_code=200)
async def home_endpoint(response: Response, user=Depends(get_user_data)):
    if not user:
        response.status_code = 401
        return {'error': 'Unauthorized'}
    try:
        return list(
            map(article_cleanup, db_controller.get_collection().find({}, {'full_text': 0}).sort('clicks', -1).limit(6)))
    except Exception:
        traceback.print_exc()
        response.status_code = 500
        return


@app.get('/article', status_code=200)
def article_endpoint(id: str, response: Response, query: str = None, user=Depends(get_user_data)):
    if not user:
        response.status_code = 401
        return {'error': 'Unauthorized'}
    try:
        record = db_controller.get_collection().find_one({
            '$or': [
                {'pmc_id': id}, {'id': id}, {'_id': id}
            ]})
        if record is None:
            response.status_code = 404
            return "Article not found"

        article: FullArticle
        if ('where' in record and record['where'] == "Pubmed") \
                or ('source' in record and record['source'] in ['Pubmed', 'PMC']):
            article = FullPMCArticle(record, query)
        elif record['source'] == "Incyte":
            article = FullIncyteArticle(record, query)
        else:
            raise NotImplementedError("Unknown source")

        article.db_save()
        return article.to_dict()
    except PDFException as e:
        response.status_code = 314
        response.headers['location'] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{e.pmc_id}"
        return "PDF exception - redirecting to PMC"
    except Exception as e:
        logger.exception(e)
        response.status_code = 500
        return


@app.get('/download_pdf', status_code=200)
def download_pdf_endpoint(id: str, response: Response, user=Depends(get_user_data)):
    if not user:
        response.status_code = 401
        return {'error': 'Unauthorized'}
    try:
        if id.startswith("PMC") and "pdf" not in id:
            s = HTMLSession()
            url = f'https://www.ncbi.nlm.nih.gov/pmc/articles/{id}/'
            r = s.get(url=url, timeout=5)
            try:
                pdf_url = 'https://www.ncbi.nlm.nih.gov' + r.html.find('a.int-view', first=True).attrs['href']
                response.status_code = 200
                return {"path": pdf_url}
            except Exception:
                response.status_code = 303
                response.headers['location'] = url
        else:
            incyte_article = db_controller.get_collection().find_one({
                '$or': [
                    {'pmc_id': id}, {'id': id}, {'_id': id}
                ]})
            return {"path": incyte_article.path}
    except Exception as e:
        logger.exception(e)
        response.status_code = 500
        return


@app.get("/internal/flush-cache")
async def flush_cache_endpoint():
    cache.flush()
    return {"message": "Cache flushed"}


@app.get("/internal/configure-index")
async def configure_index_endpoint():
    meilisearch_client.configure_settings()
    return {"message": "Index configured"}


@app.get("/dangerous/delete-incyte-articles")
async def delete_incyte_articles_endpoint():
    meilisearch_client.delete_all_documents()
    db_controller.get_collection().delete_many({'source': 'Incyte'})
    return {"message": "Incyte articles deleted"}


# mount router from routers/auth.py
app.include_router(auth_router, tags=["auth"])

if __name__ == '__main__':
    uvicorn.run("top_level:top", port=8080, host="0.0.0.0", reload=True)
