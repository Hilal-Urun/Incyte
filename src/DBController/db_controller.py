import os
import sys

from pymongo import MongoClient, ReturnDocument


class DBController:
    def __init__(self):
        self.__client = None
        self.__db = None

    def connect(self):
        try:
            self.__client = MongoClient(
                host=os.getenv('DB_HOST'),
                port=int(os.getenv('DB_PORT', '27017')),
                username=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                tls=os.getenv('DB_TLS') is not None,
                tlsAllowInvalidCertificates=True,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                serverSelectionTimeoutMS=5000,
                retryWrites=False
            )
            self.__db = self.__client[os.getenv('DB_NAME', 'incyte')]
        except Exception as e:
            print(str(e), file=sys.stderr)
            exit(1)

    def disconnect(self):
        if self.__client is not None:
            self.__client.close()
        self.__client = None
        self.__db = None

    def connection_test(self):
        try:
            self.connect()
            self.get_db().command('ping')
            return True
        except Exception as e:
            print(f"DB connection failed: {str(e)}", file=sys.stderr)
            exit(1)

    def get_db(self):
        if self.__client is not None and self.__db is not None:
            return self.__db

        self.connect()
        return self.__db

    def get_collection(self):
        try:
            collection = self.get_db().articles
            return collection
        except Exception as e:
            return {"db_error": str(e)}

    def update_record(self, obj):
        try:

            set_obj = {}
            # print(obj.keys())

            if 'keywords' in obj.keys():
                set_obj.update({'keywords': obj['keywords']})

            if 'full_text' in obj.keys():
                set_obj.update({'full_text': obj['full_text']})

            if 'counter' in obj.keys():
                set_obj.update({'counter': obj['counter']})

            if 'abstract' in obj.keys():
                set_obj.update({'abstract': obj['abstract']})

            print(set_obj)

            updated_article = self.get_collection().find_one_and_update(
                {'pmc_id': obj['pmc_id']},
                {'$set': set_obj},
                return_document=ReturnDocument.AFTER
            )
            return updated_article

        except Exception as e:
            return {"db_error": str(e)}

    def tag_search(self, keyword):
        articles = self.get_collection().find({'keywords': keyword})
        # calcul the length of the cursor because cursor is not serializable
        results = list(articles)
        print(len(results))
        if len(results) == 0:
            return []

        else:
            return results

    def id_search(self, ids: list[str]):
        articles = self.get_collection().find({'_id': {'$in': ids}})
        # calcul the length of the cursor because cursor is not serializable
        results = list(articles)
        print(len(results))
        if len(results) == 0:
            return []
        else:
            return results
