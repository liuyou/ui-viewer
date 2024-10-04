# -*- coding: utf-8 -*-

import os
import webbrowser
import uvicorn

from fastapi import FastAPI
from fastapi import Request
from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse

from uiviewer._models import ApiResponse
from uiviewer._device import list_serials, init_device, cached_devices


app = FastAPI()


current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ApiResponse(success=False, message=str(exc)).dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(success=False, message=exc.detail).dict(),
    )


def open_browser():
    webbrowser.open_new("http://127.0.0.1:8000")


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/health")
async def health():
    return "ok"


@app.get("/{platform}/serials", response_model=ApiResponse)
async def get_serials(platform: str):
    serials = list_serials(platform)
    return ApiResponse.doSuccess(serials)


@app.post("/{platform}/{serial}/init", response_model=ApiResponse)
async def init(platform: str, serial: str):
    device = init_device(platform, serial)
    return ApiResponse.doSuccess(device)


@app.get("/{platform}/{serial}/screenshot", response_model=ApiResponse)
async def screenshot(platform: str, serial: str):
    device = cached_devices.get((platform, serial))
    data = device.take_screenshot()
    return ApiResponse.doSuccess(data)


@app.get("/{platform}/{serial}/hierarchy", response_model=ApiResponse)
async def dump_hierarchy(platform: str, serial: str):
    device = cached_devices.get((platform, serial))
    data = device.dump_hierarchy()
    return ApiResponse.doSuccess(data)


if __name__ == "__main__":
    import threading
    threading.Timer(1.0, open_browser).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)