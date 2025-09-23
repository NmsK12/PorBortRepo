from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Optional

import httpx
import requests
from bs4 import BeautifulSoup

from .config import get_settings


class IntranetClient:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: Optional[httpx.AsyncClient] = None
        self._is_logged_in: bool = False
        self._reniec_tokens: Dict[str, str] = {}

    async def __aenter__(self) -> "IntranetClient":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.stop()

    async def start(self) -> None:
        if self._client is None:
            timeout = httpx.Timeout(60.0, connect=30.0, read=60.0, write=30.0)
            # Headers simples para evitar problemas con CodeIgniter
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
            }
            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=timeout,
                follow_redirects=True,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )

    async def stop(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self._is_logged_in = False
            self._reniec_tokens = {}

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

        # Warmup: visitar main y login para cookies
        try:
            await self._client.get(self._settings.main_url)
            await self._client.get(self._settings.login_url)
        except Exception:
            pass

        # Login
        resp = await self._client.post(self._settings.login_url, data=form_data)
        resp.raise_for_status()
        self._is_logged_in = True

        # PIDE
        await self._client.post(
            self._settings.pide_form_url,
            headers={
                **self._client.headers,
                "Referer": self._settings.main_url,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        
        # IMPORTANTE: Visitar main después de pideForm (como en el flujo real)
        await self._client.get(self._settings.main_url)
        
        # RENIEC form (obtener tokens ocultos)
        await self._fetch_reniec_tokens()
        
        # IMPORTANTE: Esperar un poco para que el servidor procese
        import asyncio
        await asyncio.sleep(1)
        
        # DEBUG: Verificar cookies actuales
        print(f"Cookies después del flujo: {[c.name for c in self._client.cookies.jar]}")
        
        # IMPORTANTE: Hacer login real para obtener cookies válidas
        try:
            print("Iniciando login real...")
            
            # 1. Visitar página de login para obtener cookies iniciales
            login_page = await self._client.get(self._settings.login_url)
            print(f"Login page status: {login_page.status_code}")
            
            # 2. Hacer login real con credenciales correctas
            form_data = {
                "txtUser": self._settings.intranet_user,
                "txtClave": self._settings.intranet_password,
            }
            
            login_resp = await self._client.post(
                self._settings.login_url, 
                data=form_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": self._settings.login_url,
                }
            )
            print(f"Login response status: {login_resp.status_code}")
            print(f"Login response URL: {login_resp.url}")
            
            # 3. Verificar que el login fue exitoso
            if "main" not in str(login_resp.url) and login_resp.status_code != 200:
                raise Exception(f"Login falló - Status: {login_resp.status_code}, URL: {login_resp.url}")
                
            print(f"Login exitoso, cookies obtenidas: {[c.name for c in self._client.cookies.jar]}")
            
            # 4. Visitar main para establecer sesión completa
            await self._client.get(self._settings.main_url)
            
            # Marcar como logueado
            self._is_logged_in = True
            
        except Exception as e:
            print(f"Error en login real: {e}")
            # Fallback: usar cookie hardcodeada si el login falla
            fresh_cookie = "a:34:{s:10:\"session_id\";s:32:\"f3cf6dcc1b830fdcdf8168878682a0fc\";s:10:\"ip_address\";s:10:\"10.10.1.22\";s:10:\"user_agent\";s:120:\"Mozilla/5.0+(Windows+NT+10.0;+Win64;+x64)+AppleWebKit/537.36+(KHTML,+like+Gecko)+Chrome/140.0.0.0+Safari/537.36+Edg/140.\";s:13:\"last_activity\";i:1758663930;s:9:\"user_data\";s:0:\"\";s:17:\"intra_user_nombre\";s:13:\"EDGAR+ANTONIO\";s:8:\"intra_ip\";b:0;s:16:\"intra_s_empleado\";i:43;s:15:\"intra_s_oficina\";i:240;s:13:\"intra_s_cargo\";i:561;s:15:\"intra_s_entidad\";s:1:\"1\";s:12:\"intra_s_anio\";s:4:\"2025\";s:13:\"intra_es_jefe\";b:0;s:16:\"intra_s_oficinan\";s:17:\"AREA+DE+ESCALAFON\";s:14:\"intra_s_cargon\";s:8:\"EMPLEADO\";s:15:\"intra_s_periodo\";i:6700;s:19:\"intra_es_mesapartes\";b:0;s:15:\"intra_s_mesa_id\";s:0:\"\";s:14:\"intra_user_nom\";s:13:\"EDGAR+ANTONIO\";s:15:\"intra_user_ape1\";s:5:\"PINTO\";s:15:\"intra_user_ape2\";s:6:\"DUARTE\";s:24:\"intra_es_responsable_sis\";s:0:\"\";s:20:\"intra_es_informatica\";b:0;s:14:\"intra_username\";s:10:\"JESCALAFON\";s:15:\"intra_host_name\";s:26:\"BOLPE_DEV.MUNITACNA.GOB.PE\";s:9:\"intra_doc\";s:8:\"00469746\";s:9:\"intra_rol\";i:5;s:14:\"intra_rol_nomb\";s:9:\"PIDE+TODO\";s:13:\"intra_persona\";i:43;s:14:\"intra_password\";s:8:\"jave*123\";s:18:\"intra_is_logged_in\";s:1:\"1\";s:14:\"intra_user_dni\";s:8:\"00469746\";s:10:\"reniec_dni\";s:0:\"\";s:16:\"reniec_resultado\";s:0:\"\";}06b7eacd5947107806786bdc7fef4c7d"
            self._client.cookies.set("ci_session", fresh_cookie, domain=".munitacna.gob.pe")
            print(f"Usando cookie de fallback: {fresh_cookie[:50]}...")
            self._is_logged_in = True

    async def _fetch_reniec_tokens(self) -> None:
        assert self._client is not None
        reniec_resp = await self._client.post(
            self._settings.reniec_form_url,
            headers={
                **self._client.headers,
                "Referer": self._settings.main_url,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        soup = BeautifulSoup(reniec_resp.text, "lxml")
        tokens: Dict[str, str] = {}
        for inp in soup.find_all("input"):
            name = inp.get("name")
            if not name:
                continue
            itype = inp.get("type", "").lower()
            if itype in ("hidden", "text"):
                tokens[name] = inp.get("value", "")
        for key in ("csrf_token", "csrf_test_name", "ci_csrf_token", "token"):
            if key in tokens and tokens[key]:
                continue
            el = soup.find("input", attrs={"name": key})
            if el:
                tokens[key] = el.get("value", "")
        self._reniec_tokens = tokens

    async def get_reniec_form_debug(self) -> Dict[str, Any]:
        await self.ensure_login()
        assert self._client is not None
        await self._fetch_reniec_tokens()
        # Devolver inputs y una vista previa del HTML
        resp = await self._client.post(
            self._settings.reniec_form_url,
            headers={
                **self._client.headers,
                "Referer": self._settings.main_url,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        html = resp.text
        return {
            "status_code": resp.status_code,
            "inputs": self._reniec_tokens,
            "cookies": {c.name: c.value for c in self._client.cookies.jar},
            "html_preview": html[:1000] + ("..." if len(html) > 1000 else ""),
        }

    def test_manual_request(self, dni: str) -> Dict[str, Any]:
        """Método de prueba con petición completamente manual"""
        import urllib.request
        import urllib.parse
        
        # Usar la cookie fresca
        fresh_cookie = "a:34:{s:10:\"session_id\";s:32:\"f3cf6dcc1b830fdcdf8168878682a0fc\";s:10:\"ip_address\";s:10:\"10.10.1.22\";s:10:\"user_agent\";s:120:\"Mozilla/5.0+(Windows+NT+10.0;+Win64;+x64)+AppleWebKit/537.36+(KHTML,+like+Gecko)+Chrome/140.0.0.0+Safari/537.36+Edg/140.\";s:13:\"last_activity\";i:1758663930;s:9:\"user_data\";s:0:\"\";s:17:\"intra_user_nombre\";s:13:\"EDGAR+ANTONIO\";s:8:\"intra_ip\";b:0;s:16:\"intra_s_empleado\";i:43;s:15:\"intra_s_oficina\";i:240;s:13:\"intra_s_cargo\";i:561;s:15:\"intra_s_entidad\";s:1:\"1\";s:12:\"intra_s_anio\";s:4:\"2025\";s:13:\"intra_es_jefe\";b:0;s:16:\"intra_s_oficinan\";s:17:\"AREA+DE+ESCALAFON\";s:14:\"intra_s_cargon\";s:8:\"EMPLEADO\";s:15:\"intra_s_periodo\";i:6700;s:19:\"intra_es_mesapartes\";b:0;s:15:\"intra_s_mesa_id\";s:0:\"\";s:14:\"intra_user_nom\";s:13:\"EDGAR+ANTONIO\";s:15:\"intra_user_ape1\";s:5:\"PINTO\";s:15:\"intra_user_ape2\";s:6:\"DUARTE\";s:24:\"intra_es_responsable_sis\";s:0:\"\";s:20:\"intra_es_informatica\";b:0;s:14:\"intra_username\";s:10:\"JESCALAFON\";s:15:\"intra_host_name\";s:26:\"BOLPE_DEV.MUNITACNA.GOB.PE\";s:9:\"intra_doc\";s:8:\"00469746\";s:9:\"intra_rol\";i:5;s:14:\"intra_rol_nomb\";s:9:\"PIDE+TODO\";s:13:\"intra_persona\";i:43;s:14:\"intra_password\";s:8:\"jave*123\";s:18:\"intra_is_logged_in\";s:1:\"1\";s:14:\"intra_user_dni\";s:8:\"00469746\";s:10:\"reniec_dni\";s:0:\"\";s:16:\"reniec_resultado\";s:0:\"\";}06b7eacd5947107806786bdc7fef4c7d"
        
        data = urllib.parse.urlencode({"txtDni": dni}).encode('utf-8')
        
        req = urllib.request.Request(
            self._settings.dni_api_url,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://app.munitacna.gob.pe/intranet/main",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
                "Cookie": f"ci_session={fresh_cookie}",
            }
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
                return {
                    "status_code": response.status,
                    "html_length": len(html),
                    "html_preview": html[:1000] + ("..." if len(html) > 1000 else ""),
                    "payload_sent": {"txtDni": dni},
                }
        except Exception as e:
            return {"error": str(e)}

    def test_with_requests(self, dni: str) -> Dict[str, Any]:
        """Método de prueba usando requests en lugar de httpx"""
        session = requests.Session()
        
        # Usar la cookie fresca
        fresh_cookie = "a:34:{s:10:\"session_id\";s:32:\"f3cf6dcc1b830fdcdf8168878682a0fc\";s:10:\"ip_address\";s:10:\"10.10.1.22\";s:10:\"user_agent\";s:120:\"Mozilla/5.0+(Windows+NT+10.0;+Win64;+x64)+AppleWebKit/537.36+(KHTML,+like+Gecko)+Chrome/140.0.0.0+Safari/537.36+Edg/140.\";s:13:\"last_activity\";i:1758663930;s:9:\"user_data\";s:0:\"\";s:17:\"intra_user_nombre\";s:13:\"EDGAR+ANTONIO\";s:8:\"intra_ip\";b:0;s:16:\"intra_s_empleado\";i:43;s:15:\"intra_s_oficina\";i:240;s:13:\"intra_s_cargo\";i:561;s:15:\"intra_s_entidad\";s:1:\"1\";s:12:\"intra_s_anio\";s:4:\"2025\";s:13:\"intra_es_jefe\";b:0;s:16:\"intra_s_oficinan\";s:17:\"AREA+DE+ESCALAFON\";s:14:\"intra_s_cargon\";s:8:\"EMPLEADO\";s:15:\"intra_s_periodo\";i:6700;s:19:\"intra_es_mesapartes\";b:0;s:15:\"intra_s_mesa_id\";s:0:\"\";s:14:\"intra_user_nom\";s:13:\"EDGAR+ANTONIO\";s:15:\"intra_user_ape1\";s:5:\"PINTO\";s:15:\"intra_user_ape2\";s:6:\"DUARTE\";s:24:\"intra_es_responsable_sis\";s:0:\"\";s:20:\"intra_es_informatica\";b:0;s:14:\"intra_username\";s:10:\"JESCALAFON\";s:15:\"intra_host_name\";s:26:\"BOLPE_DEV.MUNITACNA.GOB.PE\";s:9:\"intra_doc\";s:8:\"00469746\";s:9:\"intra_rol\";i:5;s:14:\"intra_rol_nomb\";s:9:\"PIDE+TODO\";s:13:\"intra_persona\";i:43;s:14:\"intra_password\";s:8:\"jave*123\";s:18:\"intra_is_logged_in\";s:1:\"1\";s:14:\"intra_user_dni\";s:8:\"00469746\";s:10:\"reniec_dni\";s:0:\"\";s:16:\"reniec_resultado\";s:0:\"\";}06b7eacd5947107806786bdc7fef4c7d"
        
        session.cookies.set("ci_session", fresh_cookie, domain=".munitacna.gob.pe")
        
        payload = {"txtDni": dni}
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://app.munitacna.gob.pe/intranet/main",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
        }
        
        resp = session.post(self._settings.dni_api_url, data=payload, headers=headers)
        
        return {
            "status_code": resp.status_code,
            "html_length": len(resp.text),
            "html_preview": resp.text[:1000] + ("..." if len(resp.text) > 1000 else ""),
            "payload_sent": payload,
        }

    async def consultar_dni(self, dni: str) -> Dict[str, Any]:
        await self.ensure_login()
        assert self._client is not None

        # Limpiar y validar DNI - solo números
        dni_limpio = ''.join(filter(str.isdigit, dni))
        if len(dni_limpio) != 8:
            return {"ok": False, "dni": dni, "mensaje": "DNI debe tener exactamente 8 dígitos"}
        
        # El portal solo necesita txtDni (como en el flujo real)
        payload = {"txtDni": dni_limpio}
        resp = await self._client.post(
            self._settings.dni_api_url,
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://app.munitacna.gob.pe/intranet/main",
            },
        )
        resp.raise_for_status()

        html = resp.text
        soup = BeautifulSoup(html, "lxml")

        datos: Dict[str, Any] = {}

        table = soup.find("table", id="table") or (soup.find_all("table")[0] if soup.find_all("table") else None)
        if table:
            for tr in table.find_all("tr"):
                celdas = tr.find_all("td")
                if len(celdas) == 2:
                    clave = celdas[0].get_text(strip=True).replace(" ", "_").replace(".", "").lower()
                    valor = celdas[1].get_text(strip=True)
                    datos[clave] = valor

        foto_b64: Optional[str] = None
        foto_tag = soup.find("img", id="img_foto")
        if foto_tag and foto_tag.get("src") and "base64" in foto_tag["src"]:
            foto_b64 = foto_tag["src"]

        if not datos or "mensaje" in datos:
            result: Dict[str, Any] = {}
            if foto_b64:
                result["foto_base64"] = foto_b64
            result["dni"] = dni
            result["mensaje"] = datos.get("mensaje", "No se encontraron datos para el DNI consultado")
            result["ok"] = False
            return result

        prefer_order = [
            "foto_base64",
            "dni",
            "nombres",
            "apellido_paterno",
            "apellido_materno",
            "dirección",
            "direccion",
            "ubigeo",
            "restricción",
            "restriccion",
            "estado_civil",
        ]

        base: Dict[str, Any] = {**datos}
        base["dni"] = dni_limpio
        if foto_b64:
            base["foto_base64"] = foto_b64

        result: Dict[str, Any] = {}
        for key in prefer_order:
            if key in base:
                result[key] = base.pop(key)
        for key in list(base.keys()):
            result[key] = base[key]
        result["ok"] = True
        return result


async def _main_debug() -> None:
    from pprint import pprint

    client = IntranetClient()
    async with client:
        data = await client.consultar_dni("00000000")
        pprint(data)


if __name__ == "__main__":
    asyncio.run(_main_debug())
