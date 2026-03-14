# ServantX Backend

Minimal FastAPI backend for ServantX.

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running

Start the development server:

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
