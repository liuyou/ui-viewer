# -*- coding: utf-8 -*-

import abc
import tempfile
from typing import List, Dict, Union, Tuple
from functools import cached_property  # python3.8+

from PIL import Image
import tidevice
import adbutils
import wda
import uiautomator2 as u2
from hmdriver2 import hdc
from hmdriver2.driver import Driver
from fastapi import HTTPException

from uiviewer._utils import file_to_base64, image_to_base64
from uiviewer._models import Platform, BaseHierarchy
from uiviewer.parser import android_hierarchy, ios_hierarchy, harmony_hierarchy


def list_serials(platform: str) -> List[str]:
    devices = []
    if platform == Platform.ANDROID:
        raws = adbutils.AdbClient().device_list()
        devices = [item.serial for item in raws]
    elif platform == Platform.IOS:
        raw = tidevice.Usbmux().device_list()
        devices = [d.udid for d in raw]
    elif platform == Platform.HARMONY:
        devices = hdc.list_devices()
    else:
        raise HTTPException(status_code=200, detail="Unsupported platform")

    return devices


class DeviceMeta(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def take_screenshot(self) -> str:
        pass

    def dump_hierarchy(self) -> Dict:
        pass


class HarmonyDevice(DeviceMeta):
    def __init__(self, serial: str):
        self.serial = serial
        self.client = Driver(serial)

    @cached_property
    def display_size(self) -> Tuple:
        return self.client.display_size

    def take_screenshot(self) -> str:
        with tempfile.NamedTemporaryFile(delete=True, suffix=".png") as f:
            path = f.name
            self.client.screenshot(path)
            return file_to_base64(path)

    def dump_hierarchy(self) -> BaseHierarchy:
        packageName, pageName = self.client.current_app()
        raw: Dict = self.client.dump_hierarchy()
        hierarchy: Dict = harmony_hierarchy.convert_harmony_hierarchy(raw)
        return BaseHierarchy(
            jsonHierarchy=hierarchy,
            activityName=pageName,
            packageName=packageName,
            windowSize=self.display_size,
            scale=1
        )


class AndroidDevice(DeviceMeta):
    def __init__(self, serial: str):
        self.serial = serial
        self.d: u2.Device = u2.connect(serial)

    @cached_property
    def window_size(self) -> Tuple:
        return self.d.window_size()

    def take_screenshot(self) -> str:
        img: Image.Image = self.d.screenshot()
        return image_to_base64(img)

    def dump_hierarchy(self) -> BaseHierarchy:
        current = self.d.app_current()
        page_xml = self.d.dump_hierarchy()
        page_json = android_hierarchy.get_android_hierarchy(page_xml)
        return BaseHierarchy(
            jsonHierarchy=page_json,
            activityName=current['activity'],
            packageName=current['package'],
            windowSize=self.window_size,
            scale=1
        )


class IosDevice(DeviceMeta):
    def __init__(self, udid: str, wda_url: str) -> None:
        self.udid = udid
        self.client = wda.Client(wda_url)

    @cached_property
    def scale(self) -> int:
        return self.client.scale

    @cached_property
    def window_size(self) -> Tuple:
        return self.client.window_size()

    def take_screenshot(self) -> str:
        img: Image.Image = self.client.screenshot()
        return image_to_base64(img)

    def dump_hierarchy(self) -> BaseHierarchy:
        data: Dict = self.client.source(format="json")
        hierarchy: Dict = ios_hierarchy.convert_ios_hierarchy(data, self.scale)
        return BaseHierarchy(
            jsonHierarchy=hierarchy,
            activityName=None,
            packageName=self.client.bundle_id,
            windowSize=self.window_size,
            scale=self.scale
        )


def get_device(platform: str, serial: str, wda_url: str = None) -> Union[HarmonyDevice, AndroidDevice]:
    if serial not in list_serials(platform):
        raise HTTPException(status_code=200, detail="Device not found")
    if platform == Platform.HARMONY:
        return HarmonyDevice(serial)
    elif platform == Platform.ANDROID:
        return AndroidDevice(serial)
    elif platform == Platform.IOS:
        return IosDevice(serial, wda_url)
    else:
        raise HTTPException(status_code=200, detail="Unsupported platform")


# Global cache for devices
cached_devices = {}


def init_device(platform: str, serial: str, wda_url: str = None):
    device = get_device(platform, serial, wda_url)
    cached_devices[(platform, serial)] = device
    return platform, serial