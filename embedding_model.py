
from base_class import Embedding_Model
import pickle
from sentence_transformers import SentenceTransformer

from openai.embeddings_utils import (
    get_embedding,
)


class HuggingfaceSentenceTransformerModel(Embedding_Model):
    EMBEDDING_MODEL = "distiluse-base-multilingual-cased-v2"

    def __init__(self, model_name=EMBEDDING_MODEL) -> None:
        super().__init__(model_name)
        
        self.model = SentenceTransformer(model_name)

    def __call__(self, text) -> None:
        return self.model.encode(text)


class OpenAIEmbeddingModel(Embedding_Model):
    # constants
    EMBEDDING_MODEL = "text-embedding-ada-002"
    # establish a cache of embeddings to avoid recomputing
    # cache is a dict of tuples (text, model) -> embedding, saved as a pickle file

    def __init__(self, model_name=EMBEDDING_MODEL) -> None:
        super().__init__(model_name)
        self.model_name = model_name

    # define a function to retrieve embeddings from the cache if present, and otherwise request via the API
    def embedding_from_string(self,
                              string: str,
                              ) -> list:
        """Return embedding of given string, using a cache to avoid recomputing."""
        model = self.model_name
        if (string, model) not in self.embedding_cache.keys():
            self.embedding_cache[(string, model)] = get_embedding(
                string, model)
            with open(self.embedding_cache_path, "wb") as embedding_cache_file:
                pickle.dump(self.embedding_cache, embedding_cache_file)
        return self.embedding_cache[(string, model)]

    def __call__(self, text) -> None:
        return self.embedding_from_string(text)
