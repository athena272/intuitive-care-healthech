"""Descoberta e download dos ZIPs de demonstracoes contabeis (ultimos N trimestres)."""

import re
import logging
from pathlib import Path
from urllib.parse import urljoin

import requests

from config import BASE_URL, NUM_QUARTERS, OUTPUT_DIR

logger = logging.getLogger(__name__)


def _parse_index_links(html: str, base: str) -> list[str]:
    """Extrai links (href) de uma pagina de indice Apache."""
    # Links no formato <a href="2025/"> ou <a href="1T2025.zip">
    pattern = re.compile(r'<a\s+href="([^"]+)"', re.IGNORECASE)
    found = []
    for match in pattern.finditer(html):
        href = match.group(1).strip()
        if href in ("../", "/", "?", "..") or href.startswith("?"):
            continue
        full = urljoin(base + "/" if not base.endswith("/") else base, href)
        found.append(full)
    return found


def _is_year_dir(url: str) -> bool:
    """Retorna True se o link parece ser um diretorio de ano (ex: 2024, 2025)."""
    segment = url.rstrip("/").split("/")[-1]
    return segment.isdigit() and len(segment) == 4 and 2000 <= int(segment) <= 2100


def _parse_quarter_zip(url: str) -> tuple[int, int] | None:
    """De uma URL como .../1T2025.zip retorna (ano, trimestre) ou None."""
    segment = url.rstrip("/").split("/")[-1]
    # Formato 1T2025, 2T2025, 3T2025, 4T2025
    m = re.match(r"^([1-4])T(\d{4})\.zip$", segment, re.IGNORECASE)
    if not m:
        return None
    return int(m.group(2)), int(m.group(1))


def discover_quarter_zips() -> list[tuple[str, int, int]]:
    """
    Descobre os ultimos NUM_QUARTERS trimestres disponiveis.
    Retorna lista de (url_zip, ano, trimestre) ordenada do mais recente ao mais antigo.
    """
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; ANS-ETL/1.0)"})

    # Listar anos
    resp = session.get(BASE_URL)
    resp.raise_for_status()
    base_with_trailing = BASE_URL.rstrip("/") + "/"
    links = _parse_index_links(resp.text, BASE_URL)
    year_dirs = [u for u in links if _is_year_dir(u)]
    year_dirs.sort(key=lambda u: u.split("/")[-2], reverse=True)

    all_quarters: list[tuple[str, int, int]] = []
    for year_url in year_dirs:
        r = session.get(year_url)
        r.raise_for_status()
        year_links = _parse_index_links(r.text, year_url)
        for link in year_links:
            pq = _parse_quarter_zip(link)
            if pq:
                ano, trim = pq
                all_quarters.append((link, ano, trim))

    all_quarters.sort(key=lambda x: (x[1], x[2]), reverse=True)
    selected = all_quarters[:NUM_QUARTERS]
    logger.info("Trimestres selecionados: %s", [(a, t) for _, a, t in selected])
    return selected


def download_zips(
    quarter_list: list[tuple[str, int, int]], dest_dir: str | Path | None = None
) -> list[Path]:
    """Baixa cada ZIP no diretorio dest_dir. Retorna lista de paths dos ZIPs baixados."""
    dest_dir = Path(dest_dir or OUTPUT_DIR)
    dest_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; ANS-ETL/1.0)"})
    downloaded = []
    for url, ano, trim in quarter_list:
        fname = f"{trim}T{ano}.zip"
        path = dest_dir / fname
        try:
            r = session.get(url, timeout=120)
            r.raise_for_status()
            path.write_bytes(r.content)
            downloaded.append(path)
            logger.info("Baixado: %s -> %s", url, path)
        except Exception as e:
            logger.warning("Falha ao baixar %s: %s", url, e)
    return downloaded
