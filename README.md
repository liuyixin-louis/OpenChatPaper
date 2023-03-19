# ChatPaper

## Setup
> prepare an (OpenAI API key)[https://platform.openai.com/account/api-keys]
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

## References
1. SciPDF Parser: https://github.com/titipata/scipdf_parser 
2. St-chat: https://github.com/AI-Yash/st-chat
3. Sentence-transformers: https://github.com/UKPLab/sentence-transformers
4. https://github.com/acheong08/ChatGPT