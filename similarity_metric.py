from base_class import SimilarityAlg
from openai.embeddings_utils import (
    distances_from_embeddings,
)


class CosineSimilarity(SimilarityAlg):
    def __init__(self) -> None:
        pass

    @staticmethod
    def __call__(query_embedding, embeddings) -> None:
        return distances_from_embeddings(query_embedding, embeddings, distance_metric="cosine")
