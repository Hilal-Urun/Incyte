from __future__ import annotations

import os

from loguru import logger
import pypeln as pl

from Classes.Article import IncyteArticle
from indexing.meilisearch.meilisearch_client import MeilisearchClient
from grobid_client_ex import GrobidClient
from sharepoint.sharepoint_client import IncyteSharePointClient, IncyteSPDoc, FormatAdapter


class IncyteSharepointCrawler:
    grobid_client = GrobidClient()
    sp_client = IncyteSharePointClient()
    meilisearch_client = MeilisearchClient()

    def crawl(self, query):
        logger.info(f"Starting crawl for query: {query}")
        results = self.sp_client.search(query)
        stage = pl.task.map(self.process_sp_doc, results,
                            workers=int(os.environ.get('SP_CRAWL_PARALLELIZATION_FACTOR', 1)))
        return list(stage)

    def process_sp_doc(self, sp_doc: IncyteSPDoc) -> IncyteArticle | None:
        logger.info(f"Processing SP doc: {sp_doc}")
        if sp_doc.ContentBuffer is None:
            sp_doc.ContentBuffer = self.sp_client.download_file(sp_doc.Path)

        sp_doc = FormatAdapter.to_pdf(sp_doc)
        tei = self.grobid_client.extract_pdf_headers(sp_doc.ContentBuffer)
        if tei is None:
            logger.error(f"Failed to extract headers from {sp_doc}")
            return None
        logger.success("Successfully processed SP doc: " + str(sp_doc))
        article = IncyteArticle(obj={
            **sp_doc.to_dict(),
            **tei
        }, query='')
        if not self.article_eligible_for_indexing(article):
            logger.warning(f"Article {article} is not eligible for indexing")
            return None

        logger.info("Saving article to index")
        self.meilisearch_client.add_document(article)
        logger.success(f"Successfully saved article {article} to index")

        logger.info(f"Persisting article: {article} to DB")
        article.persist()
        logger.success(f"Successfully persisted article: {article} to DB")
        return article

    def article_eligible_for_indexing(self, article: IncyteArticle) -> bool:
        # rudimentary for now
        return article.title is not None and article.title != '' and article.abstract is not None and article.abstract != ''
        pass
