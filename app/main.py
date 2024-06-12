import os
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from openai import AsyncOpenAI
from dotenv import load_dotenv
from uuid import uuid4
import markdown
from pygments.formatters import HtmlFormatter
from fastapi.staticfiles import StaticFiles

# Load environment variables from .env file
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="app/templates")

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# In-memory storage for sessions
sessions = {}

# Password for login
LOGIN_PASSWORD = os.environ.get("LOGIN_PASSWORD")

# Model from environment variable
MODEL_NAME = os.environ.get("MODEL_NAME", "Unknown Model")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("chat.html", {"request": request, "model_name": MODEL_NAME})

@app.post("/new-chat", response_class=HTMLResponse)
async def new_chat(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]
    session_id = str(uuid4())
    sessions[session_id] = []
    response = templates.TemplateResponse("chat_box.html", {"request": request})
    response.set_cookie(key="session_id", value=session_id)
    return response

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, password: str = Form(...)):
    if password == LOGIN_PASSWORD:
        session_id = str(uuid4())
        sessions[session_id] = []
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="session_id", value=session_id)
        return response
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/send-message", response_class=HTMLResponse)
async def send_message(request: Request, message: str = Form(...)):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")

    messages = sessions[session_id]

    # Add user's message to the session context
    messages.append({"role": "user", "content": message})

    # Send the conversation history to OpenAI
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
    )
    
    chat_response = response.choices[0].message.content
    
    # Add assistant's response to the session context
    messages.append({"role": "assistant", "content": chat_response})
    sessions[session_id] = messages
    
    # Convert the chat response from Markdown to HTML
    chat_response_html = markdown.markdown(chat_response, extensions=['fenced_code', 'codehilite'])
    css = HtmlFormatter().get_style_defs('.codehilite')

    return templates.TemplateResponse("chat_messages.html", {
        "request": request,
        "user_message": message,
        "chat_response": chat_response_html,
        "css": css
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
