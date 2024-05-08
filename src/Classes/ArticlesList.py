import os
from threading import Thread

import requests
from pymongo import ReplaceOne

from Classes.Article import Article
from DBController import db_controller


class ArticlesList(list[Article]):
    def __init__(self, articles: list[Article]):
        super().__init__(articles)

    def rank(self, query: str):
        abstracts = [" ".join(article.keywords) + " ".join(article.lemmas) for article in self]

        bi_encoder_scores = requests.post(f"{os.environ.get('TORCHSERVE_BASE_URL')}/predictions/bi_encoder",
                                          json={"text": abstracts, "query": query}).json()

        for score in bi_encoder_scores:
            self[score['corpus_id']].set_score(float(score['score']))

        self.sort(key=lambda x: x.score, reverse=True)

    def _db_save(self):
        mongo_ops = [ReplaceOne(
            {'_id': article.id},
            article.to_dict(),
            upsert=True
        ) for article in self if article.source != "Incyte"]  # Incyte articles are already saved on the fly
        if len(mongo_ops) > 0:
            db_controller.get_collection().bulk_write(mongo_ops)

    def db_save(self):
        Thread(target=self._db_save).start()
