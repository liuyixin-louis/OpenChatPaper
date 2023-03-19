# ChatPaper

## Setup

1. Install dependencies (tested on Python 3.9)

```bash
 pip install -r requirements.txt
```

2. Setup GROBID local server

```bash
bash serve_grobid.sh
```

3. Setup backend

```bash
python backend.py --port 5000 --host localhost
```

4. Frontend 

```bash
streamlit run frontend.py --server.port 8502 --server.host localhost
```

## Demo Example

> Temporary demo website: http://5e2f-128-180-213-119.ngrok.io/

- Prepare an [OpenAI API key](https://platform.openai.com/account/api-keys) and then upload a PDF to start chatting with the paper. 

![image-20230318232056584](https://s2.loli.net/2023/03/19/SbsuLQJpdqePoZV.png)

## TODO

- [ ] **Context Condense**: how to deal with long context? maybe we can tune a soft prompt to condense the context
- [ ] **Poping context out based on similarity**: now we simply pop out the first QA-pair when we encounter the maximum token limit

## References

1. SciPDF Parser: https://github.com/titipata/scipdf_parser 
2. St-chat: https://github.com/AI-Yash/st-chat
3. Sentence-transformers: https://github.com/UKPLab/sentence-transformers
4. https://github.com/acheong08/ChatGPT