import os
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Template, TemplateNotFound

from .constants import ANALYTICS_API, API_PREFIX, APP_NAME, IS_DEV
from .database.sql import create_tables
from .logger import logger
from .routers import analytics
from .times import utc_now
from .version import __version__

origins = ["*"]

NOT_AUTHORIZED = "Not Authorized"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title=APP_NAME,
    lifespan=lifespan,
    docs_url="/docs" if IS_DEV else None,
    redoc_url=None,
    contact={
        "name": "Ivo Bellin Salarin",
        "email": "ivo@nilleb.com",
    },
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(API_PREFIX)
def read_api_root():
    return {"status": "ok", "version": __version__, "name": APP_NAME}


app.include_router(analytics.router, prefix=API_PREFIX)


TEMPLATES = {}


def lazy_templates_loader():
    if "templates" not in TEMPLATES:
        current_file_folder = os.path.dirname(os.path.abspath(__file__))
        static_folder = os.path.join(current_file_folder, "../static")
        templates = Jinja2Templates(directory=static_folder)
        TEMPLATES["templates"] = templates
    return TEMPLATES["templates"]


@app.get("/{rest_of_path:path}", include_in_schema=False)
async def catch_all(
    request: Request,
    rest_of_path: str,
):
    if rest_of_path.startswith("latest/meta-data"):
        raise HTTPException(status_code=404, detail="Not found")

    context = {
        "request": request,
        "base_url": str(request.base_url).rstrip("/"),
        "API_PREFIX": API_PREFIX,
        "ANALYTICS_API": ANALYTICS_API,
    }
    try:
        path = (
            f"{rest_of_path}index.html" if rest_of_path.endswith("/") else rest_of_path
        )
        response = lazy_templates_loader().TemplateResponse(
            path,
            context,
        )
        response.headers["Expires"] = (utc_now() + timedelta(hours=1)).strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )
        return response
    except TemplateNotFound:
        logger.exception(f"Template not found: index.html when serving {rest_of_path}")
        with open("static/index.html") as f:
            template_str = f.read()
            template = Template(template_str)
            return HTMLResponse(template.render(context))
