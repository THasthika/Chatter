from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Response, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from chatter.manager import ChatterManager
from fastapi.templating import Jinja2Templates
from chatter.utils import Gender
from dotenv import load_dotenv
import os

load_dotenv()

WEBSOCKET_URL = os.environ.get("WEBSOCKET_URL", "ws://127.0.0.1:8000/ws")
GA_ID = os.environ.get("GA_ID", None)

chatter: ChatterManager | None = None


def get_chatter_manager() -> ChatterManager:
    if chatter is None:
        raise Exception("Manager not initiated!")
    return chatter


@asynccontextmanager
async def lifespan(app: FastAPI):
    global chatter
    chatter = ChatterManager()
    yield
    await chatter.close()

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/health")
async def health():
    return Response("Working...")


@app.get("/user-count")
async def user_count():
    chatter = get_chatter_manager()
    return JSONResponse({"user_count": chatter.get_user_count()})


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "genders": [str(g) for g in Gender],
        "ages": [i for i in range(0, 101)],
        "websocket_url": WEBSOCKET_URL,
        "ga_id": GA_ID
    })


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        chatter = get_chatter_manager()
        await websocket.accept()
        await chatter.handle_websocket(websocket)
    except TimeoutError:
        print("Timeout Error")
        await chatter.remove_websocket(websocket)
    except WebSocketDisconnect:
        print("Websocket Disconnect")
        await chatter.remove_websocket(websocket)
    except Exception as e:
        print(e)
        await chatter.remove_websocket(websocket)
