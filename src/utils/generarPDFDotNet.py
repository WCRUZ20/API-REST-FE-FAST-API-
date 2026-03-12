import os
import httpx

class DotNetCrystalClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def health(self) -> str:
        url = f"{self.base_url}/health"
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url)
        r.raise_for_status()
        return r.text

    async def render_factura01(self, payload: dict, output_pdf_path: str) -> str:
        url = f"{self.base_url}/render/factura01"

        timeout = httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                url,
                json=payload,
                headers={"Accept": "application/pdf"},
            )

        if r.status_code >= 400:
            # .NET suele devolver error detallado; intentamos leerlo
            ct = (r.headers.get("content-type") or "").lower()
            if "application/json" in ct:
                try:
                    detail = r.json()
                except Exception:
                    detail = r.text
            else:
                detail = r.text
            raise RuntimeError(f"Error {r.status_code} desde .NET: {detail}")

        ct = (r.headers.get("content-type") or "").lower()
        if "application/pdf" not in ct:
            raise RuntimeError(f"Content-Type inesperado ({ct}). Body: {r.text[:500]}")

        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
        with open(output_pdf_path, "wb") as f:
            f.write(r.content)

        return output_pdf_path

    async def render_notacredito(self, payload: dict, output_pdf_path: str) -> str:
        url = f"{self.base_url}/render/notacredito"

        timeout = httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                url,
                json=payload,
                headers={"Accept": "application/pdf"},
            )

        if r.status_code >= 400:
            # .NET suele devolver error detallado; intentamos leerlo
            ct = (r.headers.get("content-type") or "").lower()
            if "application/json" in ct:
                try:
                    detail = r.json()
                except Exception:
                    detail = r.text
            else:
                detail = r.text
            raise RuntimeError(f"Error {r.status_code} desde .NET: {detail}")

        ct = (r.headers.get("content-type") or "").lower()
        if "application/pdf" not in ct:
            raise RuntimeError(f"Content-Type inesperado ({ct}). Body: {r.text[:500]}")

        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
        with open(output_pdf_path, "wb") as f:
            f.write(r.content)

        return output_pdf_path
    
    async def render_retencion(self, payload: dict, output_pdf_path: str) -> str:
        url = f"{self.base_url}/render/retencion"

        timeout = httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                url,
                json=payload,
                headers={"Accept": "application/pdf"},
            )

        if r.status_code >= 400:
            # .NET suele devolver error detallado; intentamos leerlo
            ct = (r.headers.get("content-type") or "").lower()
            if "application/json" in ct:
                try:
                    detail = r.json()
                except Exception:
                    detail = r.text
            else:
                detail = r.text
            raise RuntimeError(f"Error {r.status_code} desde .NET: {detail}")

        ct = (r.headers.get("content-type") or "").lower()
        if "application/pdf" not in ct:
            raise RuntimeError(f"Content-Type inesperado ({ct}). Body: {r.text[:500]}")

        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
        with open(output_pdf_path, "wb") as f:
            f.write(r.content)

        return output_pdf_path

    async def render_notadebito(self, payload: dict, output_pdf_path: str) -> str:
        url = f"{self.base_url}/render/notadebito"

        timeout = httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                url,
                json=payload,
                headers={"Accept": "application/pdf"},
            )

        if r.status_code >= 400:
            # .NET suele devolver error detallado; intentamos leerlo
            ct = (r.headers.get("content-type") or "").lower()
            if "application/json" in ct:
                try:
                    detail = r.json()
                except Exception:
                    detail = r.text
            else:
                detail = r.text
            raise RuntimeError(f"Error {r.status_code} desde .NET: {detail}")

        ct = (r.headers.get("content-type") or "").lower()
        if "application/pdf" not in ct:
            raise RuntimeError(f"Content-Type inesperado ({ct}). Body: {r.text[:500]}")

        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
        with open(output_pdf_path, "wb") as f:
            f.write(r.content)

        return output_pdf_path
    
    async def render_guiaremision(self, payload: dict, output_pdf_path: str) -> str:
        url = f"{self.base_url}/render/guiaremision"

        timeout = httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                url,
                json=payload,
                headers={"Accept": "application/pdf"},
            )

        if r.status_code >= 400:
            # .NET suele devolver error detallado; intentamos leerlo
            ct = (r.headers.get("content-type") or "").lower()
            if "application/json" in ct:
                try:
                    detail = r.json()
                except Exception:
                    detail = r.text
            else:
                detail = r.text
            raise RuntimeError(f"Error {r.status_code} desde .NET: {detail}")

        ct = (r.headers.get("content-type") or "").lower()
        if "application/pdf" not in ct:
            raise RuntimeError(f"Content-Type inesperado ({ct}). Body: {r.text[:500]}")

        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
        with open(output_pdf_path, "wb") as f:
            f.write(r.content)

        return output_pdf_path
    
    async def render_liquidacioncompra(self, payload: dict, output_pdf_path: str) -> str:
        url = f"{self.base_url}/render/liquidacioncompra"

        timeout = httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                url,
                json=payload,
                headers={"Accept": "application/pdf"},
            )

        if r.status_code >= 400:
            # .NET suele devolver error detallado; intentamos leerlo
            ct = (r.headers.get("content-type") or "").lower()
            if "application/json" in ct:
                try:
                    detail = r.json()
                except Exception:
                    detail = r.text
            else:
                detail = r.text
            raise RuntimeError(f"Error {r.status_code} desde .NET: {detail}")

        ct = (r.headers.get("content-type") or "").lower()
        if "application/pdf" not in ct:
            raise RuntimeError(f"Content-Type inesperado ({ct}). Body: {r.text[:500]}")

        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
        with open(output_pdf_path, "wb") as f:
            f.write(r.content)

        return output_pdf_path