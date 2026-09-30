# page_publicacao.py
"""
Etapa final da contratação no ComprasNet.

Fluxo:
  1. Clica em #concluir-contratacao ("Concluir").
  2. Aguarda a confirmação e clica em "Divulgar a contratação".
  3. Aguarda a tela/modal de recibo.
  4. Salva a página de recibo em PDF dentro de ./recibos.
  5. Clica em "FECHAR".
  6. Retorna ao main.py, que pode seguir para o próximo processo.

Observação:
O PDF é gerado pelo Chrome DevTools (Page.printToPDF), equivalente ao
Ctrl+P + "Salvar como PDF", porém sem depender da janela nativa do Windows.
"""

from __future__ import annotations

import base64
import re
from datetime import datetime
from pathlib import Path
from typing import List

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config
from logger import get_logger
from models import ItemContratacao
from utils_dom import wait_dom_stable


log = get_logger(__name__)
TIMEOUT = config.TIMEOUT


BTN_CONCLUIR = (
    By.ID,
    "concluir-contratacao",
)

BTN_DIVULGAR = (
    By.XPATH,
    "//button[normalize-space(.)='Divulgar a contratação']",
)

BTN_FECHAR_RECIBO = (
    By.XPATH,
    "//button[normalize-space(.)='FECHAR']",
)


def _wait(driver, timeout: int | None = None) -> WebDriverWait:
    return WebDriverWait(
        driver,
        timeout or TIMEOUT,
    )


def _elemento_visivel(driver, locator):
    for elemento in driver.find_elements(
        *locator
    ):
        try:
            if elemento.is_displayed():
                return elemento
        except StaleElementReferenceException:
            continue

    return False


def _click_visivel(
    driver,
    locator,
    *,
    timeout: int | None = None,
    descricao: str,
) -> None:
    """
    Clica uma única vez no elemento visível.
    Não possui retry de gravação para evitar publicação duplicada.
    """
    elemento = _wait(
        driver,
        timeout,
    ).until(
        lambda d: _elemento_visivel(
            d,
            locator,
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center', inline:'nearest'});",
        elemento,
    )

    try:
        elemento.click()
    except ElementClickInterceptedException:
        driver.execute_script(
            "arguments[0].click();",
            elemento,
        )

    log.info(
        "Clique executado: %s.",
        descricao,
    )


def _processo_do_item(
    item: ItemContratacao,
) -> str:
    return str(
        getattr(
            item,
            "processo",
            None,
        )
        or getattr(
            item,
            "PROCESSO",
            None,
        )
        or ""
    ).strip()


def _nome_seguro(
    processo: str,
) -> str:
    nome = re.sub(
        r'[\\/:*?"<>|]+',
        "-",
        processo.strip(),
    )

    nome = re.sub(
        r"\s+",
        "_",
        nome,
    )

    return nome or "processo"


def _caminho_recibo(
    processo: str,
) -> Path:
    config.RECIBOS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    base = config.RECIBOS_DIR / (
        f"recibo_{_nome_seguro(processo)}.pdf"
    )

    if not base.exists():
        return base

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return config.RECIBOS_DIR / (
        f"recibo_{_nome_seguro(processo)}_{timestamp}.pdf"
    )


def _salvar_pdf_recibo(
    driver,
    processo: str,
) -> Path:
    """
    Gera o PDF diretamente pelo Chrome DevTools.

    Isso evita a janela nativa aberta por Ctrl+P, que não é controlada
    pelo Selenium e poderia interromper o fluxo automático.
    """
    destino = _caminho_recibo(
        processo
    )

    log.info(
        "Gerando PDF do recibo: %s",
        destino,
    )

    resultado = driver.execute_cdp_cmd(
        "Page.printToPDF",
        {
            "printBackground": True,
            "preferCSSPageSize": True,
        },
    )

    dados_base64 = resultado.get(
        "data",
        "",
    )

    if not dados_base64:
        raise RuntimeError(
            "O Chrome não retornou os dados do PDF do recibo."
        )

    dados = base64.b64decode(
        dados_base64
    )

    if not dados.startswith(
        b"%PDF"
    ):
        raise RuntimeError(
            "O conteúdo retornado pelo Chrome não é um PDF válido."
        )

    destino.write_bytes(
        dados
    )

    if not destino.exists() or destino.stat().st_size == 0:
        raise RuntimeError(
            f"O recibo não foi gravado corretamente em: {destino}"
        )

    log.info(
        "✓ Recibo salvo: %s | %.1f KB",
        destino,
        destino.stat().st_size / 1024,
    )

    return destino


def _aguardar_recibo(
    driver,
) -> None:
    """
    Considera o recibo pronto quando o botão FECHAR da tela/modal final
    estiver visível.
    """
    try:
        _wait(
            driver
        ).until(
            lambda d: _elemento_visivel(
                d,
                BTN_FECHAR_RECIBO,
            )
        )

    except TimeoutException as exc:
        raise RuntimeError(
            "A contratação foi divulgada, mas a tela de recibo "
            "não apareceu dentro do tempo esperado."
        ) from exc

    wait_dom_stable(
        driver
    )

    log.info(
        "Tela de recibo carregada."
    )


def _fechar_recibo(
    driver,
) -> None:
    log.info(
        "Fechando recibo..."
    )

    _click_visivel(
        driver,
        BTN_FECHAR_RECIBO,
        descricao="FECHAR recibo",
    )

    try:
        _wait(
            driver
        ).until(
            lambda d: not _elemento_visivel(
                d,
                BTN_FECHAR_RECIBO,
            )
        )
    except TimeoutException:
        log.warning(
            "O botão FECHAR foi clicado, mas ainda foi localizado na tela."
        )

    wait_dom_stable(
        driver
    )


def executar_processo(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:
    """
    Publica UMA contratação e salva seu recibo antes de devolver
    o controle ao orquestrador.
    """
    if not itens_processo:
        raise ValueError(
            "Nenhum registro recebido em Publicação."
        )

    processos = {
        _processo_do_item(
            item
        )
        for item in itens_processo
        if _processo_do_item(
            item
        )
    }

    if len(
        processos
    ) != 1:
        raise RuntimeError(
            "Publicação recebeu registros de mais de um processo: "
            + ", ".join(
                sorted(
                    processos
                )
            )
        )

    processo = next(
        iter(
            processos
        )
    )

    log.info(
        "▶ PUBLICAÇÃO | processo=%s",
        processo,
    )

    log.info(
        "Clicando em Concluir..."
    )

    _click_visivel(
        driver,
        BTN_CONCLUIR,
        descricao="Concluir contratação",
    )

    wait_dom_stable(
        driver
    )

    log.info(
        "Confirmando 'Divulgar a contratação'..."
    )

    try:
        _wait(
            driver
        ).until(
            lambda d: _elemento_visivel(
                d,
                BTN_DIVULGAR,
            )
        )
    except TimeoutException as exc:
        raise RuntimeError(
            "Após clicar em Concluir, o botão "
            "'Divulgar a contratação' não apareceu."
        ) from exc

    _click_visivel(
        driver,
        BTN_DIVULGAR,
        descricao="Divulgar a contratação",
    )

    _aguardar_recibo(
        driver
    )

    recibo = _salvar_pdf_recibo(
        driver,
        processo,
    )

    _fechar_recibo(
        driver
    )

    log.info(
        "✓ PUBLICAÇÃO CONCLUÍDA | processo=%s | recibo=%s",
        processo,
        recibo.name,
    )
