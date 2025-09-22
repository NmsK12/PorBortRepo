from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import httpx
from bs4 import BeautifulSoup

from .config import get_settings


class IntranetClient:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: Optional[httpx.AsyncClient] = None
        self._is_logged_in: bool = False

    async def __aenter__(self) -> "IntranetClient":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.stop()

    async def start(self) -> None:
        if self._client is None:
            timeout = httpx.Timeout(30.0, connect=30.0)
            self._client = httpx.AsyncClient(
                headers=self._settings.default_headers,
                timeout=timeout,
                follow_redirects=True,
            )

    async def stop(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self._is_logged_in = False

    async def ensure_login(self) -> None:
        if self._client is None:
            await self.start()
        if self._is_logged_in:
            return
        assert self._client is not None

        form_data = {
            "txtUser": self._settings.intranet_user,
            "txtClave": self._settings.intranet_password,
        }

        # Warmup GET opcional para cookies
        try:
            await self._client.get(self._settings.login_url)
        except Exception:
            pass

        resp = await self._client.post(self._settings.login_url, data=form_data)
        resp.raise_for_status()
        self._is_logged_in = True

    async def consultar_dni(self, dni: str) -> Dict[str, Any]:
        await self.ensure_login()
        assert self._client is not None

        # El portal espera el campo 'txtDni'
        payload = {"txtDni": dni}
        resp = await self._client.post(self._settings.dni_api_url, data=payload)
        resp.raise_for_status()

        html = resp.text
        soup = BeautifulSoup(html, "lxml")

        datos: Dict[str, Any] = {}

        # Tabla con id 'table'
        table = soup.find("table", id="table")
        if table:
            for tr in table.find_all("tr"):
                celdas = tr.find_all("td")
                if len(celdas) == 2:
                    clave = celdas[0].get_text(strip=True).replace(" ", "_").replace(".", "").lower()
                    valor = celdas[1].get_text(strip=True)
                    datos[clave] = valor

        # Foto base64 si existe
        foto_b64: Optional[str] = None
        foto_tag = soup.find("img", id="img_foto")
        if foto_tag and foto_tag.get("src") and "base64" in foto_tag["src"]:
            foto_b64 = foto_tag["src"]

        # Si hay mensaje de error o no hay datos, devolvemos estructura clara (sin HTML)
        if not datos or "mensaje" in datos:
            result: Dict[str, Any] = {}
            if foto_b64:
                result["foto_base64"] = foto_b64
            result["dni"] = dni
            result["mensaje"] = datos.get("mensaje", "No se encontraron datos para el DNI consultado")
            result["ok"] = False
            return result

        # Orden preferido de salida
        prefer_order = [
            "foto_base64",
            "dni",
            "nombres",
            "apellido_paterno",
            "apellido_materno",
            "dirección",
            "direccion",  # por si llega sin tilde
            "ubigeo",
            "restricción",
            "restriccion",  # por si llega sin tilde
            "estado_civil",
        ]

        # Base de datos a ordenar (incluimos dni y posibles claves parseadas)
        base: Dict[str, Any] = {**datos}
        base["dni"] = dni
        if foto_b64:
            base["foto_base64"] = foto_b64

        # Construimos resultado con el orden deseado
        result: Dict[str, Any] = {}
        for key in prefer_order:
            if key in base:
                result[key] = base.pop(key)

        # Agregamos el resto de claves que no estaban en el orden preferido
        for key in list(base.keys()):
            result[key] = base[key]

        # ok al final
        result["ok"] = True
        return result


# Utilidad para pruebas rápidas manuales
async def _main_debug() -> None:
    from pprint import pprint

    client = IntranetClient()
    async with client:
        data = await client.consultar_dni("00000000")
        pprint(data)


if __name__ == "__main__":
    asyncio.run(_main_debug())
