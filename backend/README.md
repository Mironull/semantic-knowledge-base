FastAPI backend for document storage with search and preview capabilities.

Supports multiple file formats: .pdf, .txt, .docx, .json, etc.

### Working with Virtual Environment

```bash
# init venv
python -m venv ./venv
# activate venv
source ./venv/bin/activate
```

```bash
# deactive venv
deactivate
```

### Installing dependencies
```bash
pip install -r requirements.txt
```

### Running a webserver with API

```bash
uvicorn main:app --reload
```

API will be available on http://127.0.0.1:8000
API DOCS - http://127.0.0.1:8000/docs 