# FastAPI Application

A modern Python API built with FastAPI.

## Features

- FastAPI framework with automatic API documentation
- Pydantic models for data validation
- CORS middleware enabled
- Environment variable configuration
- RESTful API endpoints

## Getting Started

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

5. Open [http://localhost:8000](http://localhost:8000) to view the API
6. View interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs)

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check
- `POST /items/` - Create a new item
- `GET /items/` - Get all items
- `GET /items/{item_id}` - Get specific item
- `PUT /items/{item_id}` - Update item
- `DELETE /items/{item_id}` - Delete item

## Development

- The API includes automatic interactive documentation
- Hot reload is enabled during development
- All endpoints include proper error handling
