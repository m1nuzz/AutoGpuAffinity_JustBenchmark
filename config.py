import logging
import os
from configparser import ConfigParser
from dataclasses import dataclass
from enum import Enum

LOG_CONFIG = logging.getLogger("CONFIG")


class Api(Enum):
    LIBLAVA = 1
    D3D9 = 2


@dataclass
class Settings:
    cache_duration: int
    benchmark_duration: int
    api: Api
    skip_confirmation: bool


@dataclass
class Liblava:
    fullscreen: bool
    x_resolution: int
    y_resolution: int
    fps_cap: int
    triple_buffering: bool


class Config:
    def __init__(self, config_path: str):
        if not os.path.exists(config_path):
            error_msg = f"config file not found at path: {config_path}"
            LOG_CONFIG.error(error_msg)
            raise FileNotFoundError(error_msg)

        config = ConfigParser(delimiters="=")
        config.read(config_path)

        apis: dict[int, Api] = {
            1: Api.LIBLAVA,
            2: Api.D3D9,
        }

        self.settings = Settings(
            cache_duration=config.getint("settings", "cache_duration"),
            benchmark_duration=config.getint("settings", "benchmark_duration"),
            api=apis[config.getint("settings", "api")],
            skip_confirmation=config.getboolean("settings", "skip_confirmation"),
        )

        self.liblava = Liblava(
            config.getboolean("liblava", "fullscreen"),
            config.getint("liblava", "x_resolution"),
            config.getint("liblava", "y_resolution"),
            config.getint("liblava", "fps_cap"),
            config.getboolean("liblava", "triple_buffering"),
        )

    def validate_config(self):
        errors = 0

        if self.settings.cache_duration < 0 or self.settings.benchmark_duration <= 0:
            LOG_CONFIG.error("invalid durations specified")
            errors += 1

        if self.settings.api not in Api:
            LOG_CONFIG.error("invalid api specified")
            errors += 1

        return 1 if errors else 0
