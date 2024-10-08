# -*- coding: utf-8 -*-

from typing import Union, Optional

from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse

from uiviewer._device import (
    list_serials,
    init_device,
    cached_devices,
    AndroidDevice,
    IosDevice,
    HarmonyDevice
)
from uiviewer._models import ApiResponse
from uiviewer._version import __version__


router = APIRouter()


@router.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@router.get("/health")
def health():
    return "ok"


@router.get("/version", response_model=ApiResponse)
def get_version():
    return ApiResponse.doSuccess(__version__)


@router.get("/{platform}/serials", response_model=ApiResponse)
def get_serials(platform: str):
    serials = list_serials(platform)
    return ApiResponse.doSuccess(serials)


@router.post("/{platform}/{serial}/connect", response_model=ApiResponse)
def connect(
    platform: str,
    serial: str,
    wdaUrl: Union[str, None] = Query(None),
    maxDepth: Union[int, None] = Query(None)
):
    ret = init_device(platform, serial, wdaUrl, maxDepth)
    return ApiResponse.doSuccess(ret)


@router.get("/{platform}/{serial}/screenshot", response_model=ApiResponse)
def screenshot(platform: str, serial: str):
    device: Union[AndroidDevice, IosDevice, HarmonyDevice] = cached_devices.get((platform, serial))
    data = device.take_screenshot()
    return ApiResponse.doSuccess(data)


@router.get("/{platform}/{serial}/hierarchy", response_model=ApiResponse)
def dump_hierarchy(platform: str, serial: str):
    device: Union[AndroidDevice, IosDevice, HarmonyDevice] = cached_devices.get((platform, serial))
    data = device.dump_hierarchy()
    return ApiResponse.doSuccess(data)