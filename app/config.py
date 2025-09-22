from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict

from dotenv import load_dotenv

# Cargar variables desde .env si existe
load_dotenv()


@dataclass(frozen=True)
class Settings:
    intranet_user: str
    intranet_password: str
    login_url: str
    dni_api_url: str
    default_headers: Dict[str, str]


def get_settings() -> Settings:
    intranet_user = os.getenv("INTRA_USER", "")
    intranet_password = os.getenv("INTRA_PASS", "")

    if not intranet_user or not intranet_password:
        # Permitimos levantar la app, pero los endpoints fallarán con 500 si falta config
        # para que el operador sepa que debe configurar el .env
        pass

    login_url = (
        os.getenv(
            "LOGIN_URL",
            "https://app.munitacna.gob.pe/intranet/login/login/index",
        )
    )
    dni_api_url = (
        os.getenv(
            "DNI_API_URL",
            "https://app.munitacna.gob.pe/intranet/pide/reniecBuscar",
        )
    )

    default_headers: Dict[str, str] = {
        "User-Agent": os.getenv(
            "HTTP_USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
        ),
        "Referer": os.getenv("HTTP_REFERER", "https://app.munitacna.gob.pe/intranet/main"),
        "Origin": os.getenv("HTTP_ORIGIN", "https://app.munitacna.gob.pe"),
        "X-Requested-With": "XMLHttpRequest",
    }

    return Settings(
        intranet_user=intranet_user,
        intranet_password=intranet_password,
        login_url=login_url,
        dni_api_url=dni_api_url,
        default_headers=default_headers,
    )
