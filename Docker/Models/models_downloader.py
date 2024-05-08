import pathlib

from sentence_transformers import SentenceTransformer


bi_encoder = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1", device="cpu")
bi_encoder.save(str(pathlib.Path().resolve().joinpath('bi_encoder')))
