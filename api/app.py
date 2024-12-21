import os
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Template, TemplateNotFound

from .common import generate_guid
from .constants import (
    ANALYTICS_API,
    ANALYTICS_HOST_PROPERTY_SLUG,
    ANALYTICS_PROPERTY_ID,
    API_PREFIX,
    APP_NAME,
    DEFAULT_PROPERTY_ID,
    IS_DEV,
    OWNER_EMAIL,
    OWNER_NAME,
    PROPERTY_SLUG,
)
from .database.sql import (
    collect,
    create_tables,
    get_or_create_property,
    get_or_create_user,
)
from .logger import logger
from .routers import analytics
from .routers.identify import identify
from .times import utc_now
from .version import __version__

origins = ["*"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    user = await get_or_create_user(
        generate_guid(OWNER_EMAIL),
        OWNER_NAME,
        OWNER_EMAIL,
    )
    await get_or_create_property(DEFAULT_PROPERTY_ID, user.id, PROPERTY_SLUG)
    await get_or_create_property(
        ANALYTICS_PROPERTY_ID, user.id, ANALYTICS_HOST_PROPERTY_SLUG
    )
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


async def log_request(data, headers, client, property_id: str):
    event = await identify(data, headers, client, property_id)
    await collect(event)


@app.get("/{rest_of_path:path}", include_in_schema=False)
async def catch_all(
    request: Request,
    rest_of_path: str,
    background_tasks: BackgroundTasks,
):
    if rest_of_path.startswith("latest/meta-data"):
        raise HTTPException(status_code=404, detail="Not found")

    fwd_proto = request.headers.get("x-forwarded-proto")
    fwd_host = request.headers.get("x-forwarded-host")
    page_url = request.headers.get("referer") or fwd_host
    data = {"page_url": page_url, "event_type": "catch_all"}
    base_url = (
        f"{fwd_proto}://{fwd_host}" if fwd_proto and fwd_host else request.base_url
    )
    background_tasks.add_task(
        log_request, data, request.headers, request.client, ANALYTICS_PROPERTY_ID
    )
    context = {
        "request": request,
        "base_url": str(base_url).rstrip("/"),
        "API_PREFIX": API_PREFIX,
        "ANALYTICS_API": ANALYTICS_API,
    }
    logger.info(
        f"catch_all: {rest_of_path}, query_params: {request.query_params}, headers: {request.headers}"
    )
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
