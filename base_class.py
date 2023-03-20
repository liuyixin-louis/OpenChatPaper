import abc
import pandas as pd
import pickle


class SimilarityAlg(metaclass=abc.ABCMeta):
    """Similarity Algorithm to compute similarity between query_embedding and embeddings"""

    def __init__(self) -> None:
        pass

    @abc.abstractmethod
    def __call__(self, query_embedding, embeddings) -> None:
        pass


class Embedding_Model(metaclass=abc.ABCMeta):
    """Embedding Model to compute embedding of a text"""

    def __init__(self, model_name) -> None:
        """Initialize the embedding model"""
        embedding_cache_path = f"/app/ckpt/embedding_cache_{model_name}.pkl"
        self.embedding_cache_path = embedding_cache_path

        # load the cache if it exists, and save a copy to disk
        try:
            embedding_cache = pd.read_pickle(embedding_cache_path)
        except FileNotFoundError:
            embedding_cache = {}
        with open(embedding_cache_path, "wb") as embedding_cache_file:
            pickle.dump(embedding_cache, embedding_cache_file)
        self.embedding_cache = embedding_cache
        self.model_name = model_name

    @abc.abstractmethod
    def __call__(self, text) -> None:
        """Compute the embedding of the text"""
        pass


class AbstractPDFParser(metaclass=abc.ABCMeta):
    """ PDF parser to parse a PDF file"""

    def __init__(self, db_name) -> None:
        """Initialize the pdf database"""
        db_cache_path = f"/app/ckpt/pdf_parser_{db_name}.pkl"
        self.db_cache_path = db_cache_path

        # load the cache if it exists, and save a copy to disk
        try:
            db_cache = pd.read_pickle(db_cache_path)
        except FileNotFoundError:
            db_cache = {}
        with open(db_cache_path, "wb") as cache_file:
            pickle.dump(db_cache, cache_file)
        self.db_cache = db_cache
        self.db_name = db_name

    @abc.abstractmethod
    def parse_pdf(self,) -> None:
        """Parse the PDF file"""
        pass

    @abc.abstractmethod
    def _get_metadata(self, ) -> None:
        """Get the metadata of the PDF file"""
        pass

    def get_paragraphs(self, ) -> None:
        """Get the paragraphs of the PDF file"""
        pass

    @abc.abstractmethod
    def get_split_paragraphs(self, ) -> None:
        """
        Get the split paragraphs of the PDF file
        Return:
            split_paragraphs: dict of metadata and corresponding list of split paragraphs
        """
        pass

    def _determine_metadata_of_paragraph(self, paragraph) -> None:
        """
        Determine the metadata of a paragraph
        Return:
            metadata: metadata of the paragraph
        """
        pass

    # @abc.abstractmethod
    # def _determine_optimal_split_of_pargraphs(self, ) -> None:
    #     """
    #     Determine the optimal split of paragraphs
    #     Return:
    #         split_paragraphs: dict of metadata and corresponding list of split paragraphs
    #     """
    #     pass


class ChatbotEngine(metaclass=abc.ABCMeta):
    def __init__(self,) -> None:
        pass

    @abc.abstractmethod
    def query(self, user_query):
        pass
