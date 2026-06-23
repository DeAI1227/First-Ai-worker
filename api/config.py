from __future__ import annotations

from project_env import load_project_env

load_project_env()

import os
from dataclasses import dataclass


@dataclass(slots=True)
class ApiSettings:
    service_name: str = "investment_research_collector"
    version: str = "mvp"
    api_auth_token: str = ""


def load_api_settings() -> ApiSettings:
    return ApiSettings(
        api_auth_token=os.getenv("API_AUTH_TOKEN", "").strip(),
    )

