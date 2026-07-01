# driver.py
"""
Fábrica do WebDriver.

Único ponto que cria o driver. Antes isso estava duplicado em main.py e
helpers.py — agora os dois consomem daqui. Conecta no Chrome já aberto em
modo Remote Debugging (autenticação manual do usuário).
"""

from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import config
from logger import get_logger

log = get_logger(__name__)


def get_driver() -> webdriver.Chrome:
    """Conecta no Chrome aberto com --remote-debugging-port."""
    options = Options()
    options.debugger_address = f"{config.CHROME_DEBUG_HOST}:{config.CHROME_DEBUG_PORT}"

    try:
        driver = webdriver.Chrome(options=options)
    except Exception as exc:  # erro de conexão é fatal e específico o suficiente
        raise RuntimeError(
            "Falha ao conectar no Chrome via Remote Debugging. "
            f"Confirme que o Chrome está aberto em "
            f"{config.CHROME_DEBUG_HOST}:{config.CHROME_DEBUG_PORT} "
            "com --remote-debugging-port."
        ) from exc

    driver.set_page_load_timeout(config.TIMEOUT)
    log.info("Conectado ao Chrome em %s:%s", config.CHROME_DEBUG_HOST, config.CHROME_DEBUG_PORT)
    return driver
