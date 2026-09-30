# page_localizar_processo.py
"""
Localização e abertura de uma contratação existente no ComprasNet.

Page reutilizável por diferentes fluxos:
  - Cadastro:
      criar contratação -> localizar contratação -> abrir edição
  - Atualização futura:
      localizar contratação -> abrir edição -> atualizar dados

Responsabilidades:
  1. selecionar o PCA correto;
  2. abrir "Contratações Minhas UASG";
  3. localizar a contratação;
  4. abrir a contratação;
  5. entrar em "Editar contratação".

A identificação atual usa:
  - título;
  - data de início;
  - data de conclusão.

Esta page NÃO altera dados da contratação.
"""

from __future__ import annotations

import unicodedata
from datetime import datetime
from typing import List, Optional, Tuple

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config
from app_selectors import S, XPATHS
from logger import get_logger
from models import ItemContratacao
from utils_dom import wait_dom_stable, wait_spinner_sumir, wclick


log = get_logger(__name__)
K = config.Constantes


class ContratacaoNaoLocalizada(TimeoutError):
    """
    Resultado normal de varredura em modo de retomada.

    Diferente de uma falha técnica: significa apenas que o processo
    testado não está presente na grade atual do PCA.
    """
    pass


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _parse_data(valor) -> Optional[Tuple[int, int, int]]:
    if isinstance(valor, tuple) and len(valor) == 3:
        return tuple(int(x) for x in valor)

    s = str(valor or "").strip()

    if not s:
        return None

    s = s.split()[0]

    for fmt in (
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%Y/%m/%d",
    ):
        try:
            d = datetime.strptime(
                s,
                fmt,
            )

            return (
                d.day,
                d.month,
                d.year,
            )

        except ValueError:
            continue

    log.warning(
        "Data não reconhecida: %r",
        valor,
    )

    return None


def _data_ddmmaaaa(valor) -> str:
    dmy = _parse_data(
        valor
    )

    if not dmy:
        return ""

    dd, mm, yyyy = dmy

    return (
        f"{dd:02d}/{mm:02d}/{yyyy:04d}"
    )


def _normalizar(texto: str) -> str:
    n = unicodedata.normalize(
        "NFD",
        str(texto or ""),
    )

    n = "".join(
        c
        for c in n
        if unicodedata.category(c) != "Mn"
    )

    for a, b in (
        ("“", '"'),
        ("”", '"'),
        ("’", "'"),
        ("‘", "'"),
        ('"', ""),
        ("'", ""),
    ):
        n = n.replace(
            a,
            b,
        )

    return " ".join(
        n.split()
    ).lower().strip()


def _celula(
    tr,
    css: str,
) -> str:
    try:
        el = tr.find_element(
            By.CSS_SELECTOR,
            css,
        )

        return (
            el.text
            or el.get_attribute(
                "innerText"
            )
            or ""
        )

    except Exception:
        return ""


# -----------------------------------------------------------------------
# PCA
# -----------------------------------------------------------------------

def _ano_pca(
    item: ItemContratacao,
) -> Optional[int]:
    dmy = (
        _parse_data(
            item.data_inicio
        )
        or _parse_data(
            item.data_conclusao
        )
    )

    return (
        dmy[2]
        if dmy
        else None
    )


def selecionar_pca(
    driver,
    item: ItemContratacao,
    timeout: int | None = None,
) -> None:
    timeout = (
        timeout
        or config.TIMEOUT
    )

    ano = _ano_pca(
        item
    )

    if ano is None:
        raise RuntimeError(
            "Não foi possível determinar o ano do PCA."
        )

    label = (
        f"PCA {ano} - {K.PCA_STATUS}"
    )

    # Evita reselecionar o mesmo PCA a cada processo durante a varredura.
    try:
        combo = driver.find_element(
            By.CSS_SELECTOR,
            S.PCA_COMBO,
        )

        texto_atual = " ".join(
            (
                combo.text
                or combo.get_attribute("innerText")
                or combo.get_attribute("aria-label")
                or combo.get_attribute("title")
                or ""
            ).split()
        )

        if _normalizar(label) in _normalizar(texto_atual):
            log.info(
                "PCA já selecionado: %s",
                label,
            )
            return

    except Exception:
        pass

    log.info(
        "Selecionando PCA: %s",
        label,
    )

    wclick(
        driver,
        S.PCA_COMBO,
        timeout,
    )

    wait_dom_stable(
        driver
    )

    wclick(
        driver,
        S.pca_opcao(
            label
        ),
        timeout,
    )

    wait_spinner_sumir(
        driver,
        timeout,
    )

    wait_dom_stable(
        driver
    )


# -----------------------------------------------------------------------
# Aba Minhas UASG
# -----------------------------------------------------------------------

def abrir_aba_minhas_uasg(
    driver,
    timeout: int | None = None,
) -> None:
    timeout = (
        timeout
        or config.TIMEOUT
    )

    linhas = driver.find_elements(
        By.CSS_SELECTOR,
        S.GRID_LINHAS,
    )

    if any(
        linha.is_displayed()
        for linha in linhas
    ):
        log.info(
            "Aba 'Contratações Minhas UASG' já está aberta."
        )
        return

    log.info(
        "Abrindo aba 'Contratações Minhas UASG'..."
    )

    wclick(
        driver,
        S.TAB_MINHAS_UASG,
        timeout,
    )

    wait_spinner_sumir(
        driver,
        timeout,
    )

    wait_dom_stable(
        driver
    )


# -----------------------------------------------------------------------
# Localizar
# -----------------------------------------------------------------------

def localizar_contratacao(
    driver,
    item: ItemContratacao,
    timeout: int | None = None,
) -> dict:
    timeout = (
        timeout
        or config.TIMEOUT
    )

    wait_spinner_sumir(
        driver,
        timeout,
    )

    WebDriverWait(
        driver,
        timeout,
    ).until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                S.GRID_LINHAS,
            )
        )
    )

    alvo_titulo = _normalizar(
        item.titulo
    )

    alvo_inicio = _data_ddmmaaaa(
        item.data_inicio
    )

    alvo_conclusao = _data_ddmmaaaa(
        item.data_conclusao
    )

    log.info(
        "Localizando contratação: título='%s' | início=%s | conclusão=%s",
        item.titulo,
        alvo_inicio,
        alvo_conclusao,
    )

    for tr in driver.find_elements(
        By.CSS_SELECTOR,
        S.GRID_LINHAS,
    ):
        titulo = _normalizar(
            _celula(
                tr,
                S.GRID_TITULO_CELULA,
            )
        )

        inicio = _celula(
            tr,
            S.GRID_INICIO_CELULA,
        ).strip()

        conclusao = _celula(
            tr,
            S.GRID_CONCLUSAO_CELULA,
        ).strip()

        titulo_ok = (
            alvo_titulo == titulo
            or alvo_titulo in titulo
            or titulo in alvo_titulo
        )

        if (
            titulo_ok
            and inicio == alvo_inicio
            and conclusao == alvo_conclusao
        ):
            tr_id = (
                tr.get_attribute("id")
                or ""
            )

            link = tr.find_element(
                By.CSS_SELECTOR,
                S.LINK_CONTRATACAO_CELULA,
            )

            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                link,
            )

            driver.execute_script(
                "arguments[0].click();",
                link,
            )

            log.info(
                "Contratação localizada (%s).",
                tr_id,
            )

            return {
                "tr_id": tr_id,
                "clicked_link": True,
            }

    raise ContratacaoNaoLocalizada(
        "Contratação não localizada: "
        f"{item.titulo} | "
        f"{alvo_inicio} | "
        f"{alvo_conclusao}"
    )


# -----------------------------------------------------------------------
# Abrir edição
# -----------------------------------------------------------------------

def abrir_edicao(
    driver,
    timeout: int | None = None,
) -> None:
    timeout = (
        timeout
        or config.TIMEOUT
    )

    log.info(
        "Abrindo edição da contratação..."
    )

    WebDriverWait(
        driver,
        timeout,
    ).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                XPATHS.botao_por_texto(
                    "Editar contratação"
                ),
            )
        )
    ).click()

    wait_dom_stable(
        driver
    )


# -----------------------------------------------------------------------
# Entrada pública
# -----------------------------------------------------------------------

def executar_processo(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:
    """
    Localiza e abre para edição a contratação de UM processo.
    """
    if not itens_processo:
        raise ValueError(
            "Nenhum registro recebido em Localizar Processo."
        )

    item = itens_processo[0]

    log.info(
        "▶ LOCALIZAR PROCESSO | processo=%s",
        item.processo,
    )

    selecionar_pca(
        driver,
        item,
    )

    abrir_aba_minhas_uasg(
        driver,
    )

    localizar_contratacao(
        driver,
        item,
    )

    abrir_edicao(
        driver,
    )

    log.info(
        "✓ Contratação localizada e aberta para edição: %s.",
        item.processo,
    )
