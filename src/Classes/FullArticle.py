import io
import os
import re
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
from threading import Thread

import requests
from grobid_client.api.pdf import process_fulltext_document
from grobid_client.models import Article as TEIArticle, ProcessForm
from grobid_client.types import File, TEI

from Classes.Article import DBArticle, s, grobidClient, expertAiClient
from Classes.Exceptions import PDFNotFoundException, PDFDownloadException
from DBController import db_controller

from sharepoint.sharepoint_client import IncyteSharePointClient
from loguru import logger


class FullArticle(DBArticle, ABC):
    def __init__(self, obj: dict, query: str):
        super().__init__(obj, query)
        self.clicks = "clicks" in obj and obj['clicks'] + 1 or 1
        if "full_text" in obj:
            self.full_text = obj['full_text']
        else:
            self.tei_article: TEIArticle = self.fetch_tei_article()
            self.full_text: dict = self.extract_full_text()
        if query is not None:
            self.paragraphs_score()

    @abstractmethod
    def fetch_tei_article(self):
        pass

    def extract_pdf(self, buffer):
        form = ProcessForm(
            input_=File(file_name=self.id, payload=buffer, mime_type="application/pdf")
        )
        logger.info(f"Extracting TEI from document: {self.id}")
        return TEI.parse(process_fulltext_document.sync_detailed(client=grobidClient, multipart_data=form).content)

    def extract_full_text(self):
        logger.info(f"Extracting full text from document: {self.id}")
        full_text = {}
        for section in self.tei_article.sections:
            if section.name is None or section.name.lower() == "title" or section.name.lower() == "abstract":
                continue
            if len(section.paragraphs) == 0:
                continue

            full_text[section.name] = {}
            full_text[section.name]['paragraphs'] = []
            for paragraph in section.paragraphs:
                if "formula" in paragraph.text.lower():
                    continue
                full_text[section.name]['paragraphs'].append({
                    'text': re.sub(
                        r"\[[0-9]+\]|Fig\. ?[0-9]+[a-zA-Z]*|\(?Table ?[0-9]+[a-zA-Z]*\)?",
                        "",
                        paragraph.text
                    )})
        logger.success(f"Extracted full text from document: {self.id}")
        return full_text

    @staticmethod
    def main_sentences_thread(paragraph):
        res = expertAiClient.specific_resource_analysis(
            body={"document": {"text": paragraph['text']}},
            params={'language': 'en', 'resource': 'relevants'}
        )
        main_sentences = [{'start': main_sentence.start, 'end': main_sentence.end} for main_sentence in
                          res.main_sentences][:3]
        paragraph.update({"main_sentences": main_sentences})

    def paragraphs_score(self):
        logger.info(f"Calculating paragraphs score for document: {self.id}")
        paragraphs = [paragraph for section in self.full_text for paragraph in self.full_text[section]['paragraphs']]
        paragraphs_list = [paragraph['text'] for paragraph in paragraphs]

        bi_encoder_scores = requests.post(f"{os.environ.get('TORCHSERVE_BASE_URL')}/predictions/bi_encoder",
                                          json={"text": paragraphs_list, "query": self.query}).json()

        for score in bi_encoder_scores:
            paragraphs[score['corpus_id']]['score'] = float(score['score'])

        with ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(self.main_sentences_thread, sorted(paragraphs, key=lambda x: x['score'], reverse=True)[0:5]))
            pool.shutdown(wait=True)

        for section in self.full_text:
            self.full_text[section]['score'] = reduce(lambda x, y: x + y,
                                                      [x['score'] for x in self.full_text[section]['paragraphs']]) \
                                               / len(self.full_text[section]['paragraphs'])
            self.full_text[section]['max_score'] = max([x['score'] for x in self.full_text[section]['paragraphs']])

        logger.success(f"Calculated paragraphs score for document: {self.id}")

    def full_text_cleanup(self):
        full_text = {}
        for section in self.full_text:
            full_text[section] = {
                'paragraphs': [{'text': paragraph['text']} for paragraph in self.full_text[section]['paragraphs']]}
        return full_text

    def to_dict(self):
        super_dict = super().to_dict()
        return {**super_dict, **{'full_text': self.full_text}}

    def _db_save(self):
        db_controller.get_collection().update_one({'_id': self.id}, {
            '$set': {'full_text': self.query and self.full_text_cleanup() or self.full_text,
                     'clicks': self.clicks}})

    def db_save(self):
        Thread(target=self._db_save).start()


class FullPMCArticle(FullArticle):
    def fetch_tei_article(self):
        logger.info(f"Fetching TEI for PMC document: {self.id}")
        url = f'https://www.ncbi.nlm.nih.gov/pmc/articles/{self.id}/'
        r = s.get(url=url, headers={
            "Content-Type": "application/json"
        }, timeout=5)
        pdf_url_tag = r.html.find('a.int-view', first=True)
        if pdf_url_tag is None:
            raise PDFNotFoundException(self.id)
        pdf_url = 'https://www.ncbi.nlm.nih.gov' + pdf_url_tag.attrs['href']
        if pdf_url is None:
            raise PDFNotFoundException(self.id)
        res = s.get(pdf_url)
        if res.status_code != 200:
            raise PDFDownloadException(self.id)

        try:
            buffer = io.BytesIO(res.content)
        except Exception as e:
            logger.error(f"Error while downloading PMC document: {self.id}")
            logger.exception(e)
            logger.error(res.ContentBuffer)
            raise PDFDownloadException(self.id)
        return self.extract_pdf(buffer)


class FullIncyteArticle(FullArticle):
    sp_client = IncyteSharePointClient()

    def __init__(self, record, query):
        self.path = record['path']
        super().__init__(record, query)

    def fetch_tei_article(self):
        logger.info(f"Downloading Incyte document: {self.id}")
        sp_file: io.BytesIO = self.sp_client.download_file(self.path)
        logger.success(f"Downloaded Incyte document: {self.id}")
        logger.info(f"Extracting TEI from Incyte document: {self.id}")
        return self.extract_pdf(sp_file)
