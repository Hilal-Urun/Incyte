import logging
from abc import ABC
from concurrent.futures import ThreadPoolExecutor

from sentence_transformers import CrossEncoder
from ts.torch_handler.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class TransformersClassifierHandler(BaseHandler, ABC):
    def __init__(self):
        super(TransformersClassifierHandler, self).__init__()
        self.initialized = False
        self.model = None

    def initialize(self, ctx):
        properties = ctx.system_properties
        model_dir = properties.get("model_dir")

        self.model = CrossEncoder(model_dir, device='cpu', max_length=512)

        self.initialized = True

    def preprocess(self, data):
        return [{'text': single['body']['text'], 'scores': single['body']['scores'], 'query': single['body']['query']}
                for single in data]

    def thread(self, text, scores, query):
        cross_inp = [[query, text[score['corpus_id']]] for score in scores]
        return [float(num) for num in self.model.predict(cross_inp)]

    def inference(self, preprocess_output):
        texts = [single['text'] for single in preprocess_output]
        scores = [single['scores'] for single in preprocess_output]
        queries = [single['query'] for single in preprocess_output]
        with ThreadPoolExecutor(max_workers=len(preprocess_output)) as pool:
            return list(pool.map(self.thread, texts, scores, queries))

    def postprocess(self, inference_output):
        return inference_output


_service = TransformersClassifierHandler()


def handle(data, context):
    try:
        if not _service.initialized:
            _service.initialize(context)

        if data is None:
            return None

        data = _service.preprocess(data)
        data = _service.inference(data)
        data = _service.postprocess(data)

        return data
    except Exception as e:
        raise e
