# page_itens.py
"""
Aba "Itens" do ComprasNet (antigo step_b).

Fluxo:
  1. abrir_itens_e_bucketizar() -> agrupa linhas consecutivas por num_processo.
  2. Para cada bucket (processo):
       - cadastrar_itens()       -> busca o código no catálogo, preenche valor/apelido.
       - localizar_e_casar_no_dc()-> envia ao DC e casa cada item por apelido + valor.
"""

from __future__ import annotations

from typing import List, Tuple

import config
from helpers import carregar_itens
from logger import get_logger
from models import ItemContratacao
from app_selectors import S
from utils_dom import (
    cur4,
    find_dc_card_by_value_and_apelido,
    find_rows_by_text,
    get_last_item_card_id,
    is_visible,
    js_set_value,
    retry_once,
    shot,
    wait_dom_stable,
    wait_text,
    wclick,
    wtype,
)

log = get_logger(__name__)
TIMEOUT = config.TIMEOUT

Bucket = Tuple[str, List[ItemContratacao]]


# ============ 1) ABRIR ITENS E CRIAR BUCKETS POR PROCESSO ============ #
def abrir_itens_e_bucketizar(driver, itens: List[ItemContratacao]) -> List[Bucket]:
    """Abre a aba Itens e cria buckets sequenciais por num_processo."""
    log.info("Abrindo aba Itens...")
    wclick(driver, S.ITENS_ABA, TIMEOUT)
    wait_dom_stable(driver)

    buckets: List[Bucket] = []
    atual_proc: str | None = None
    atual_linhas: List[ItemContratacao] = []

    for item in itens:
        proc = (item.num_processo or "").strip()
        if atual_proc is None or proc == atual_proc:
            atual_proc = proc
            atual_linhas.append(item)
        else:
            buckets.append((atual_proc, atual_linhas))
            atual_proc = proc
            atual_linhas = [item]

    if atual_linhas:
        buckets.append((atual_proc or "", atual_linhas))

    log.info("Buckets formados: %d processo(s) distinto(s).", len(buckets))
    return buckets


# ===================== 2) CADASTRAR ITENS ===================== #
@retry_once
def cadastrar_itens(driver, bucket: Bucket) -> None:
    """Para cada linha do bucket: busca o código, adiciona e preenche valor/apelido."""
    num_processo, linhas = bucket
    log.info("Cadastrando itens do processo %s...", num_processo)

    for idx, item in enumerate(linhas, start=1):
        valor_fmt = cur4(item.valor_unitario or "0")
        apelido = item.apelido
        log.info("  Item %d: apelido='%s' valor='%s'", idx, apelido, valor_fmt)

        wclick(driver, S.ADICIONAR_BTN, TIMEOUT)                 # abrir catálogo
        wtype(driver, S.CODIGO_INPUT, config.CODIGO_ITEM, clear=True)
        wclick(driver, S.LUPA_BTN, TIMEOUT)                      # pesquisar

        _selecionar_item_na_tabela(driver)
        card_id = get_last_item_card_id(driver)
        _setar_valor_e_apelido(driver, card_id, valor_fmt, apelido)
        _salvar_card(driver, card_id, valor_fmt)

        shot(driver, f"proc_{num_processo}_item_{card_id}_{apelido}.png")

    log.info("%d item(ns) cadastrado(s) no processo %s.", len(linhas), num_processo)


# ================= 3) LOCALIZAR E CASAR NO DC ================= #
@retry_once
def localizar_e_casar_no_dc(driver, bucket: Bucket) -> None:
    """Envia itens ao DC e casa cada um por apelido + valor."""
    num_processo, linhas = bucket
    log.info("Enviando itens do processo %s ao DC...", num_processo)

    wclick(driver, S.CARRINHO_BTN, TIMEOUT)
    wclick(driver, S.DC_ADD_BTN, TIMEOUT)
    if is_visible(driver, S.DC_CONFIRMAR_BTN, 2):
        wclick(driver, S.DC_CONFIRMAR_BTN, TIMEOUT)
    wait_dom_stable(driver)
    shot(driver, f"proc_{num_processo}_dc_entrada.png")

    if not is_visible(driver, S.DC_FIELDSET, TIMEOUT):
        raise RuntimeError("Fieldset do DC não ficou visível.")

    log.info("Casando cada item no DC...")
    for item in linhas:
        valor_fmt = cur4(item.valor_unitario or "0")
        apelido = item.apelido

        card_root = find_dc_card_by_value_and_apelido(
            driver, valor_fmt, apelido, scope_css=S.DC_FIELDSET
        )
        if card_root is None:
            raise RuntimeError(
                f"Item não encontrado no DC (apelido='{apelido}', valor='{valor_fmt}')."
            )

        _complementar_dc(driver, card_root, item)
        shot(driver, f"proc_{num_processo}_dc_casado_{apelido}.png")

    log.info("Itens do processo %s casados no DC.", num_processo)


# -------------------- AUXILIARES DO STEP -------------------- #
def _selecionar_item_na_tabela(driver) -> None:
    """Encontra a linha do serviço no catálogo e clica em Adicionar."""
    if not is_visible(driver, S.CATALOGO_TABELA, TIMEOUT):
        raise RuntimeError("Tabela do catálogo não visível.")
    rows = find_rows_by_text(
        driver, S.CATALOGO_TABELA, S.CATALOGO_LINHA_DESCR, config.TEXTO_SERVICO_ITEM
    )
    if not rows:
        raise RuntimeError(f"Item {config.CODIGO_ITEM} não encontrado no catálogo.")
    wclick(driver, S.CATALOGO_LINHA_BTN_ADICIONAR, TIMEOUT)
    wait_dom_stable(driver)


def _setar_valor_e_apelido(driver, card_id: str, valor_fmt: str, apelido: str) -> None:
    """Preenche valor e apelido do card (idempotente, via JS setter)."""
    js_set_value(driver, S.valor_input(card_id), valor_fmt, fire=True)
    wait_text(driver, S.valor_espelho(card_id), f"R$ {valor_fmt}", TIMEOUT)
    js_set_value(driver, S.apelido_input(card_id), apelido, fire=True)


def _salvar_card(driver, card_id: str, valor_fmt: str) -> None:
    """Salva o card e valida o espelho do valor."""
    wclick(driver, S.salvar_item(card_id), TIMEOUT)
    wait_dom_stable(driver)
    wait_text(driver, S.valor_espelho(card_id), f"R$ {valor_fmt}", TIMEOUT)


def _complementar_dc(driver, card_root, item: ItemContratacao) -> None:
    """
    Hook para campos complementares no DC (fornecedor, local de entrega, NBS...).
    A implementar com os seletores do DC.
    """
    # TODO: implementar complemento do DC.
    return


# ======================= ORQUESTRAÇÃO ======================= #
def executar(driver, itens: List[ItemContratacao]) -> None:
    """Orquestra o Step B completo (Itens + DC)."""
    for bucket in abrir_itens_e_bucketizar(driver, itens):
        cadastrar_itens(driver, bucket)
        localizar_e_casar_no_dc(driver, bucket)
    log.info("Aba Itens concluída para todos os processos.")


def run(driver) -> None:
    """Wrapper chamado pelo main.py: carrega a planilha e executa a aba Itens."""
    executar(driver, carregar_itens())
