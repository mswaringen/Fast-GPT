# FastGPT

FastAPI + HTMX chat wrapper for OpenAI API

## Run Locally

```
poetry init
uvicorn app.main:app --reload
```

## Deploy to Fly.io

Create .env with these environment variables

- OPENAI_API_KEY
- MODEL_NAME
- LOGIN_PASSWORD

```
fly launch
cat .env | fly secrets import
fly deploy
```

## Built with
- FastAPI + Jinja2
- HTMX
- Pico CSS


## Screenshot
![screenshot.png](screenshot.png)