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
    # Cliente compartido en app state
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
