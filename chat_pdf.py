
class ChatPDF():
    """ChatPDF enables us to chat with a PDF file
    """

    def __init__(self, pdf, bot, embedding_model, similarity_metric, expect_answer_token_length_max=100, expect_q_token_length_max=100, user_stamp=None) -> None:
        self.pdf = pdf
        self.bot = bot
        self.embedding_model = embedding_model
        self.similarity_metric = similarity_metric
        self.user_stamp = user_stamp

        self.system_task_prompt = f"You are a helpful PDF file. Your task is to provide information and answer any questions related to the topic of {self.pdf.metadata['title']}. You should use the sections of the PDF as your source of information and try to provide concise and accurate answers to any questions asked by the user. If you are unable to find relevant information in the given sections, you will need to let the user know that the source does not contain relevant information but still try to provide an answer based on your general knowledge. You must refer to the corresponding section name and page that you refer to when answering. The following is the related information about the PDF file that will help you answer users' questions:\n\n"
        self.system_information_prompt = "Title:\n" + self.pdf.metadata['title'] + "\n\nAbstract:\n" + self.pdf.metadata["abstract"] + \
            "\n\nFiltered paragraphs from each sections (the section titles are enclosed in asterisks**):\n\n"

        self.system_token_length = self.bot.encode_length(
            self.system_task_prompt) + self.bot.encode_length(self.system_information_prompt)
        self.expect_answer_token_length_max = expect_answer_token_length_max
        self.expect_q_token_length_max = expect_q_token_length_max
        self.context_max_length = self.bot.max_tokens - self.system_token_length - \
            self.bot.overhead_token - self.expect_answer_token_length_max - \
            self.expect_q_token_length_max

    def _get_related_context(self, user_query):
        all_contextes = [user_query]+self.pdf.flattn_paragraphs
        rank_indices = self.rank_indices(all_contextes, 0,)
        rank_indices = list(rank_indices)
        rank_indices.remove(0)
        inital_context = ":\n\n".join(self.pdf.section_names_with_page_index)
        context_dict = {section_name: []
                        for section_name in self.pdf.section_names}
        inital_context_token_length = self.bot.encode_length(inital_context)
        running_length = inital_context_token_length
        for idx in rank_indices:
            text_to_insert = all_contextes[idx]
            text_to_insert_token_length = self.bot.encode_length(
                text_to_insert)
            if running_length + text_to_insert_token_length < self.context_max_length:
                running_length += text_to_insert_token_length
                section = self.pdf.content2section[text_to_insert]
                context_dict[section].append(text_to_insert)
            else:
                break
        composed_context = ""
        for i, section_name in enumerate(self.pdf.section_names):
            if len(context_dict[section_name]) > 0:
                section_name_with_page_index = self.pdf.section_names_with_page_index[i]
                composed_context += "**"+section_name_with_page_index + "**" + \
                    ":\n" + "\n".join(context_dict[section_name]) + "\n\n"
        return composed_context

    def chat(self, user_query):
        """Chat with the PDF file
        """
        context_data = self._get_related_context(user_query)
        dynamic_system_context = self.system_task_prompt + \
            self.system_information_prompt + context_data
        print(
            "************ Start of Composed Context ************\n",
            dynamic_system_context,
            "\n************ End of Composed Context ************\n"
        )
        response = self.bot.query(
            context=dynamic_system_context, questions=user_query, convo_id=self.user_stamp)
        return response

    def rank_indices(
        self,
        strings: list[str],
        index_of_source_string: int,
    ) -> list[int]:
        """Rank the indices of the strings in the list based on their similarity to the source string."""
        # get embeddings for all strings
        embeddings = [self.embedding_model(string) for string in strings]
        # get the embedding of the source string
        query_embedding = embeddings[index_of_source_string]
        # get distances between the source embedding and other embeddings (function from embeddings_utils.py)
        distances = self.similarity_metric(query_embedding, embeddings)
        # get rank of indices based on distances
        import numpy as np
        indices_of_nearest_neighbors = np.argsort(distances, )
        return indices_of_nearest_neighbors
