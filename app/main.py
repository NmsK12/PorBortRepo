from __future__ import annotations

import re
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .http_client import IntranetClient
from .config import get_settings


dni_regex = re.compile(r"^\d{8}$")


class DniRequest(BaseModel):
    dni: str = Field(..., description="DNI de 8 dígitos", examples=["12345678"])


class ApiError(BaseModel):
    detail: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = IntranetClient()
    await app.state.client.start()
    yield
    await app.state.client.stop()


app = FastAPI(title="API Consulta DNI (Intranet Tacna)", lifespan=lifespan)


def get_client() -> IntranetClient:
    return app.state.client


async def _consultar_o_404(dni: str, client: IntranetClient) -> Dict[str, Any]:
    data = await client.consultar_dni(dni)
    if not data.get("ok"):
        raise HTTPException(status_code=404, detail=data.get("mensaje", "No encontrado"))
    return data


@app.post("/consultar-dni", response_model=dict, responses={400: {"model": ApiError}, 404: {"model": ApiError}, 500: {"model": ApiError}})
async def consultar_dni(payload: DniRequest, client: IntranetClient = Depends(get_client)) -> Dict[str, Any]:
    settings = get_settings()
    if not settings.intranet_user or not settings.intranet_password:
        raise HTTPException(status_code=500, detail="Config faltante: define INTRA_USER e INTRA_PASS en .env")

    if not dni_regex.match(payload.dni):
        raise HTTPException(status_code=400, detail="DNI inválido: debe tener 8 dígitos")

    try:
        return await _consultar_o_404(payload.dni, client)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error consultando DNI: {exc}")


@app.get("/consultar/dni/{dni}", response_model=dict, responses={400: {"model": ApiError}, 404: {"model": ApiError}, 500: {"model": ApiError}})
async def consultar_dni_path(dni: str, client: IntranetClient = Depends(get_client)) -> Dict[str, Any]:
    settings = get_settings()
    if not settings.intranet_user or not settings.intranet_password:
        raise HTTPException(status_code=500, detail="Config faltante: define INTRA_USER e INTRA_PASS en .env")

    if not dni_regex.match(dni):
        raise HTTPException(status_code=400, detail="DNI inválido: debe tener 8 dígitos")

    try:
        return await _consultar_o_404(dni, client)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error consultando DNI: {exc}")


@app.get("/debug/dni/{dni}")
async def debug_dni(dni: str, client: IntranetClient = Depends(get_client)) -> Dict[str, Any]:
    settings = get_settings()
    if not settings.intranet_user or not settings.intranet_password:
        raise HTTPException(status_code=500, detail="Config faltante")
    if not dni_regex.match(dni):
        raise HTTPException(status_code=400, detail="DNI inválido")
    try:
        await client.ensure_login()
        # Limpiar DNI como en el método principal
        dni_limpio = ''.join(filter(str.isdigit, dni))
        payload = {"txtDni": dni_limpio}
        
        resp = await client._client.post(
            settings.dni_api_url, 
            data=payload, 
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://app.munitacna.gob.pe/intranet/main",
            }
        )
        return {
            "status_code": resp.status_code,
            "html_length": len(resp.text),
            "html_preview": resp.text[:1000] + ("..." if len(resp.text) > 1000 else ""),
            "payload_sent": payload,
            "dni_limpio": dni_limpio,
            "tokens": client._reniec_tokens,
        }
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/debug/manual/{dni}")
async def debug_manual(dni: str, client: IntranetClient = Depends(get_client)) -> Dict[str, Any]:
    """Endpoint de debug usando urllib manual"""
    try:
        result = client.test_manual_request(dni)
        return result
    except Exception as exc:
        return {"error": str(exc)}

@app.get("/debug/requests/{dni}")
async def debug_requests(dni: str, client: IntranetClient = Depends(get_client)) -> Dict[str, Any]:
    """Endpoint de debug usando requests en lugar de httpx"""
    try:
        result = client.test_with_requests(dni)
        return result
    except Exception as exc:
        return {"error": str(exc)}

@app.get("/debug/simple")
async def debug_simple(client: IntranetClient = Depends(get_client)) -> Dict[str, Any]:
    """Endpoint de debug simple para probar la conexión"""
    settings = get_settings()
    try:
        await client.ensure_login()
        # Solo probar acceso a main
        resp = await client._client.get(settings.main_url)
        return {
            "status_code": resp.status_code,
            "url": str(resp.url),
            "cookies": {c.name: c.value[:50] + "..." if len(c.value) > 50 else c.value for c in client._client.cookies.jar},
        }
    except Exception as exc:
        return {"error": str(exc)}

@app.get("/debug/reniec-form")
async def debug_reniec_form(client: IntranetClient = Depends(get_client)) -> Dict[str, Any]:
    try:
        data = await client.get_reniec_form_debug()
        return data
    except Exception as exc:
        return {"error": str(exc)}
