from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import httpx
import os

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/auth/callback"

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

@app.get("/login")
def login():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": REDIRECT_URI,
        "prompt": "select_account"
    }
    url = httpx.URL(GOOGLE_AUTH_URL).include_query_params(**params)
    return RedirectResponse(str(url))

@app.get("/auth/callback")
async def auth_callback(request: Request, code: str = None):
    if not code:
        return JSONResponse({"error": "No code in request"}, status_code=400)
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }
    async with httpx.AsyncClient() as client:
        token_response = await client.post(TOKEN_URL, data=data)
        token_json = token_response.json()
    id_token = token_json.get("id_token")
    if not id_token:
        return JSONResponse({"error": "No id_token returned"}, status_code=400)
    request.session["id_token"] = id_token
    return RedirectResponse(url="/id_token")

@app.get("/id_token")
def get_id_token(request: Request):
    id_token = request.session.get("id_token")
    if not id_token:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    return {"id_token": id_token, "client_id": CLIENT_ID}
