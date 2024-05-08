import logging
from abc import ABC
from concurrent.futures import ThreadPoolExecutor

from sentence_transformers import SentenceTransformer, util
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

        self.model = SentenceTransformer(model_dir, device='cpu')

        self.model.to(self.device)
        self.model.max_seq_length = 512
        self.model.share_memory()
        self.model.eval()

        self.initialized = True

    def preprocess(self, data):
        return [{'text': single['body']['text'], 'query': single['body']['query']} for single in data]

    def thread(self, text, query):
        futures = {}
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures['query'] = pool.submit(self.model.encode, query, convert_to_tensor=True)
            futures['text'] = pool.submit(self.model.encode, text, convert_to_tensor=True)
        hits = util.semantic_search(futures['query'].result(), futures['text'].result(), top_k=len(text))
        return hits[0]

    def inference(self, preprocess_output):
        texts = [single['text'] for single in preprocess_output]
        queries = [single['query'] for single in preprocess_output]
        with ThreadPoolExecutor(max_workers=len(preprocess_output)) as pool:
            return list(pool.map(self.thread, texts, queries))

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
