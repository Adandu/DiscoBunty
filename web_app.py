from __future__ import annotations

import asyncio
import hmac
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app_state import AppState
from auth_utils import verify_password
from models import AppConfig, SaveConfigRequest, TestServerRequest


def create_web_app(state: AppState) -> FastAPI:
    app = FastAPI(title="DiscoBunty Dashboard")
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise ValueError("SECRET_KEY environment variable is mandatory for WebUI session security.")

    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key,
        session_cookie="session",
        same_site="strict",
        https_only=os.getenv("WEBUI_SECURE_COOKIES", "false").lower() == "true",
        max_age=3600,
    )

    base_dir = Path(__file__).resolve().parent
    templates = Jinja2Templates(directory=str(base_dir / "templates"))
    app.mount("/static", StaticFiles(directory=str(base_dir / "static")), name="static")

    def get_client_ip(request: Request) -> str:
        return request.client.host if request.client else "unknown"

    def is_authenticated(request: Request) -> bool:
        return bool(state.config.webui.password) and request.session.get("authenticated") is True

    def get_csrf_token(request: Request) -> str:
        token = request.session.get("csrf_token")
        if not token:
            token = secrets.token_hex(32)
            request.session["csrf_token"] = token
        return token

    def validate_csrf(request: Request) -> None:
        session_token = request.session.get("csrf_token")
        header_token = request.headers.get("X-CSRF-Token", "")
        if not session_token or not hmac.compare_digest(session_token, header_token):
            raise HTTPException(status_code=403, detail="CSRF token missing or invalid")

    def validate_csrf_form(request: Request, form_token: str) -> None:
        session_token = request.session.get("csrf_token")
        if not session_token or not form_token or not hmac.compare_digest(session_token, form_token):
            raise HTTPException(status_code=403, detail="CSRF token missing or invalid")

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: *; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        return response

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        if not is_authenticated(request):
            return RedirectResponse(url="/login")

        display_config = state.masked_config_dict()
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "config": display_config,
                "servers": display_config["servers"],
                "csrf_token": get_csrf_token(request),
            },
        )

    @app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request):
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "csrf_token": get_csrf_token(request),
                "error": request.query_params.get("error"),
            },
        )

    @app.post("/login")
    async def login(request: Request, password: str = Form(...), csrf_token: str = Form(...)):
        validate_csrf_form(request, csrf_token)
        client_ip = get_client_ip(request)
        if not state.login_limiter.is_allowed(client_ip):
            return RedirectResponse(url="/login?error=ratelimit", status_code=303)

        stored_pass = state.config.webui.password
        if not stored_pass:
            return RedirectResponse(url="/login?error=no_pass", status_code=303)

        if verify_password(password, stored_pass):
            request.session.clear()
            request.session["authenticated"] = True
            request.session["csrf_token"] = secrets.token_hex(32)
            state.login_limiter.reset(client_ip)
            return RedirectResponse(url="/", status_code=303)
        return RedirectResponse(url="/login?error=1", status_code=303)

    @app.post("/logout")
    async def logout(request: Request, csrf_token: str = Form(...)):
        validate_csrf_form(request, csrf_token)
        request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    @app.post("/api/test-server")
    async def test_server(request: Request, server_data: TestServerRequest):
        if not is_authenticated(request):
            raise HTTPException(status_code=401)
        validate_csrf(request)

        client_ip = get_client_ip(request)
        if not state.api_limiter.is_allowed(client_ip):
            raise HTTPException(status_code=429, detail="Too many requests. Please wait before testing again.")

        server_payload = server_data.model_dump(by_alias=True)
        original = next((server for server in state.config.servers if server.alias == server_data.alias), None)
        if original:
            server_payload["host"] = original.host
            server_payload["port"] = original.port
            if server_payload.get("password") == "********":
                server_payload["password"] = original.password
            if server_payload.get("key") == "********":
                server_payload["key"] = original.key

        success, message, fingerprint = await asyncio.to_thread(
            state.ssh_manager.test_server_connection,
            server_payload,
            server_data.trust_host,
        )
        return {"success": success, "message": message, "fingerprint": fingerprint}

    @app.post("/save")
    async def save_config_ui(request: Request, payload: SaveConfigRequest):
        if not is_authenticated(request):
            raise HTTPException(status_code=401)
        validate_csrf(request)

        client_ip = get_client_ip(request)
        if not state.api_limiter.is_allowed(client_ip):
            raise HTTPException(status_code=429, detail="Too many requests. Please wait before saving again.")

        body = payload.model_dump(by_alias=True)
        if "SECRET_KEY" in body:
            raise HTTPException(status_code=400, detail="SECRET_KEY rotation is not supported from the WebUI.")

        if body["discord"].get("token") == "********":
            body["discord"]["token"] = state.config.discord.token
        if body["webui"].get("password") == "********":
            body["webui"]["password"] = state.config.webui.password
        if body["features"].get("power_control_password") == "********":
            body["features"]["power_control_password"] = state.config.features.power_control_password

        original_by_alias = {server.alias: server for server in state.config.servers}
        original_by_index = list(state.config.servers)
        for index, server in enumerate(body["servers"]):
            original_alias = server.get("_original_alias") or server.get("alias")
            original = original_by_alias.get(original_alias)
            if not original and index < len(original_by_index):
                original = original_by_index[index]
            if original and server.get("password") == "********":
                server["password"] = original.password
            if original and server.get("key") == "********":
                server["key"] = original.key
            server.pop("_original_alias", None)

        new_config = AppConfig.model_validate(body)
        state.save_config(new_config)
        return {"status": "success"}

    @app.get("/api/logs")
    async def get_app_logs(request: Request):
        if not is_authenticated(request):
            raise HTTPException(status_code=401)
        return {"logs": "\n".join(list(state.log_buffer))}

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "config_loaded": True,
            "webui_enabled": state.config.webui.enabled,
            "discord_enabled": bool(state.config.discord.token),
            "servers_configured": len(state.config.servers),
        }

    return app
