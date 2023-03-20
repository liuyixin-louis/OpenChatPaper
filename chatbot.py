from base_class import ChatbotEngine
import os
import openai
import json
import os
import requests
import tiktoken
from config import MAX_TOKEN_MODEL_MAP
from utils import get_filtered_keys_from_object


class ChatbotWrapper:
    """
    Wrapper of Official ChatGPT API,
    # base on https://github.com/ChatGPT-Hackers/revChatGPT
    """

    def __init__(
        self,
        api_key: str,
        engine: str = os.environ.get("GPT_ENGINE") or "gpt-3.5-turbo",
        proxy: str = None,
        max_tokens: int = 3000,
        temperature: float = 0.5,
        top_p: float = 1.0,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        reply_count: int = 1,
        system_prompt: str = "You are ChatGPT, a large language model trained by OpenAI. Respond conversationally",
        overhead_token=96,
    ) -> None:
        """
        Initialize Chatbot with API key (from https://platform.openai.com/account/api-keys)
        """
        self.engine = engine
        self.session = requests.Session()
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.reply_count = reply_count
        self.max_limit = MAX_TOKEN_MODEL_MAP[self.engine]
        self.overhead_token = overhead_token

        if proxy:
            self.session.proxies = {
                "http": proxy,
                "https": proxy,
            }

        self.conversation: dict = {
            "default": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
            ],
        }

        if max_tokens > self.max_limit - self.overhead_token:
            raise Exception(
                f"Max tokens cannot be greater than {self.max_limit- self.overhead_token}")

        if self.get_token_count("default") > self.max_tokens:
            raise Exception("System prompt is too long")

    def add_to_conversation(
        self,
        message: str,
        role: str,
        convo_id: str = "default",
    ) -> None:
        """
        Add a message to the conversation
        """
        self.conversation[convo_id].append({"role": role, "content": message})

    def __truncate_conversation(self, convo_id: str = "default") -> None:
        """
        Truncate the conversation
        """
        # TODO: context condense with soft prompt tuning
        while True:
            if (
                self.get_token_count(convo_id) > self.max_tokens
                and len(self.conversation[convo_id]) > 1
            ):
                # Don't remove the first message and remove the first QA pair
                self.conversation[convo_id].pop(1)
                self.conversation[convo_id].pop(1)
                # TODO: optimal pop out based on similarity distance
            else:
                break

    # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    def get_token_count(self, convo_id: str = "default") -> int:
        """
        Get token count
        """
        if self.engine not in ["gpt-3.5-turbo", "gpt-3.5-turbo-0301"]:
            raise NotImplementedError("Unsupported engine {self.engine}")

        encoding = tiktoken.encoding_for_model(self.engine)

        num_tokens = 0
        for message in self.conversation[convo_id]:
            # every message follows <im_start>{role/name}\n{content}<im_end>\n
            num_tokens += 4
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += 1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens

    def get_max_tokens(self, convo_id: str) -> int:
        """
        Get max tokens
        """
        return self.max_tokens - self.get_token_count(convo_id)

    def ask_stream(
        self,
        prompt: str,
        role: str = "user",
        convo_id: str = "default",
        dynamic_system_prompt=None,
        **kwargs,
    ) -> str:
        """
        Ask a question
        """
        # Make conversation if it doesn't exist
        if convo_id not in self.conversation:
            self.reset(convo_id=convo_id, system_prompt=dynamic_system_prompt)

        # adjust system prompt
        assert dynamic_system_prompt is not None
        self.conversation[convo_id][0]["content"] = dynamic_system_prompt

        self.add_to_conversation(prompt, "user", convo_id=convo_id)
        print(" total tokens:")
        print(self.get_token_count(convo_id))
        self.__truncate_conversation(convo_id=convo_id)
        # Get response
        response = self.session.post(
            os.environ.get(
                "API_URL") or "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {kwargs.get('api_key', self.api_key)}"},
            json={
                "model": self.engine,
                "messages": self.conversation[convo_id],
                "stream": True,
                # kwargs
                "temperature": kwargs.get("temperature", self.temperature),
                "top_p": kwargs.get("top_p", self.top_p),
                "presence_penalty": kwargs.get(
                    "presence_penalty",
                    self.presence_penalty,
                ),
                "frequency_penalty": kwargs.get(
                    "frequency_penalty",
                    self.frequency_penalty,
                ),
                "n": kwargs.get("n", self.reply_count),
                "user": role,
                "max_tokens": self. get_max_tokens(convo_id=convo_id),
            },
            stream=True,
        )
        if response.status_code != 200:
            raise Exception(
                f"Error: {response.status_code} {response.reason} {response.text}",
            )
        response_role: str = None
        full_response: str = ""
        for line in response.iter_lines():
            if not line:
                continue
            # Remove "data: "
            line = line.decode("utf-8")[6:]
            if line == "[DONE]":
                break
            resp: dict = json.loads(line)
            choices = resp.get("choices")
            if not choices:
                continue
            delta = choices[0].get("delta")
            if not delta:
                continue
            if "role" in delta:
                response_role = delta["role"]
            if "content" in delta:
                content = delta["content"]
                full_response += content
                yield content
        self.add_to_conversation(
            full_response, response_role, convo_id=convo_id)

    def ask(
        self,
        prompt: str,
        role: str = "user",
        convo_id: str = "default",
        dynamic_system_prompt: str = None,
        **kwargs,
    ) -> str:
        """
        Non-streaming ask
        """
        response = self.ask_stream(
            prompt=prompt,
            role=role,
            convo_id=convo_id,
            dynamic_system_prompt=dynamic_system_prompt,
            **kwargs,
        )
        full_response: str = "".join(response)
        return full_response

    def rollback(self, n: int = 1, convo_id: str = "default") -> None:
        """
        Rollback the conversation
        """
        for _ in range(n):
            self.conversation[convo_id].pop()

    def reset(self, convo_id: str = "default", system_prompt: str = None) -> None:
        """
        Reset the conversation
        """
        self.conversation[convo_id] = [
            {"role": "system", "content": system_prompt or self.system_prompt},
        ]

    def save(self, file: str, *keys: str) -> None:
        """
        Save the Chatbot configuration to a JSON file
        """
        with open(file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    key: self.__dict__[key]
                    for key in get_filtered_keys_from_object(self, *keys)
                },
                f,
                indent=2,
                # saves session.proxies dict as session
                default=lambda o: o.__dict__["proxies"],
            )

    def load(self, file: str, *keys: str) -> None:
        """
        Load the Chatbot configuration from a JSON file
        """
        with open(file, encoding="utf-8") as f:
            # load json, if session is in keys, load proxies
            loaded_config = json.load(f)
            keys = get_filtered_keys_from_object(self, *keys)

            if "session" in keys and loaded_config["session"]:
                self.session.proxies = loaded_config["session"]
            keys = keys - {"session"}
            self.__dict__.update({key: loaded_config[key] for key in keys})


class OpenAIChatbot(ChatbotEngine):
    def __init__(self, api_key: str,
                 engine: str = os.environ.get("GPT_ENGINE") or "gpt-3.5-turbo",
                 proxy: str = None,
                 max_tokens: int = 3000,
                 temperature: float = 0.5,
                 top_p: float = 1.0,
                 presence_penalty: float = 0.0,
                 frequency_penalty: float = 0.0,
                 reply_count: int = 1,
                 system_prompt: str = "You are ChatGPT, a large language model trained by OpenAI. Respond conversationally",
                 overhead_token=96) -> None:
        openai.api_key = api_key
        self.api_key = api_key
        self.engine = engine
        self.proxy = proxy
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.reply_count = reply_count
        self.system_prompt = system_prompt

        self.bot = ChatbotWrapper(
            api_key=self.api_key,
            engine=self.engine,
            proxy=self.proxy,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty,
            reply_count=self.reply_count,
            system_prompt=self.system_prompt,
            overhead_token=overhead_token
        )
        self.overhead_token = overhead_token
        import tiktoken
        self.encoding = tiktoken.encoding_for_model(self.engine)

    def encode_length(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def query(self, questions: str,
              role: str = "user",
              convo_id: str = "default",
              context: str = None,
              **kwargs,):
        return self.bot.ask(prompt=questions, role=role, convo_id=convo_id, dynamic_system_prompt=context, **kwargs)
