# step_b.py
"""
Step B - Aba 'Itens' do ComprasNet

Fluxo:
  1. Abrir aba Itens e agrupar linhas consecutivas por num_processo.
  2. Para cada bucket (processo):
       - Cadastrar itens 21172 no catálogo com valor e apelido.
       - Enviar ao DC (carrinho) e casar cada item no DC pelo apelido + valor.
"""

import os
from typing import List, Dict, Tuple
from app_selectors import S
from helpers import apelido_from_cfg, load_all_cfgs
from utils_dom import (
    wclick, wtype, js_set_value, wait_dom_stable, wait_text, is_visible,
    find_rows_by_text, get_last_item_card_id, find_dc_card_by_value_and_apelido,
    shot, retry_once, cur4
)

TIMEOUT = int(os.getenv("TIMEOUT_SECONDS", "30"))


# ========== 1) ABRIR ITENS E CRIAR BUCKETS POR PROCESSO ==========

def abrir_itens_e_bucketizar(driver, cfg_list: List[Dict]) -> List[Tuple[str, List[Dict]]]:
    """
    Abre a aba Itens e cria buckets sequenciais por num_processo.
    'Processa até mudar de processo'.
    """
    print("🗂️ Abrindo aba Itens...")
    wclick(driver, S.ITENS_ABA, TIMEOUT)
    wait_dom_stable(driver)

    buckets = []
    atual_proc = None
    atual_linhas = []

    for cfg in cfg_list:
        proc = (cfg.get("num_processo") or "").strip()
        if atual_proc is None:
            atual_proc = proc
            atual_linhas = [cfg]
        elif proc == atual_proc:
            atual_linhas.append(cfg)
        else:
            # fechou bloco anterior
            buckets.append((atual_proc, atual_linhas))
            atual_proc = proc
            atual_linhas = [cfg]
    if atual_linhas:
        buckets.append((atual_proc, atual_linhas))

    print(f"✅ Buckets formados: {len(buckets)} processos distintos encontrados.")
    return buckets


# ========== 2) CADASTRAR ITENS 21172 ==========

@retry_once
def cadastrar_itens_21172(driver, bucket: Tuple[str, List[Dict]]):
    """
    Para cada linha do bucket:
      - Abrir catálogo e buscar 21172
      - Adicionar item “Treinamento Qualificação Profissional”
      - Preencher valor e apelido (fornecedor_nome)
      - Salvar e validar

    Usa apelido para garantir idempotência (apelido + valor + código 21172).
    """
    num_processo, linhas = bucket
    print(f"🧾 Iniciando cadastro de itens para processo {num_processo}...")

    for idx, cfg in enumerate(linhas, start=1):
        valor_fmt = cur4(cfg.get("valor", "0"))
        apelido = apelido_from_cfg(cfg)
        print(f" → Item {idx}: apelido='{apelido}', valor='{valor_fmt}'")

        # 1. abrir modal catálogo
        wclick(driver, S.ADICIONAR_BTN, TIMEOUT)

        # 2. pesquisar 21172
        wtype(driver, S.CODIGO_INPUT, "21172", clear=True)
        wclick(driver, S.LUPA_BTN, TIMEOUT)

        # 3. selecionar linha alvo
        selecionar_21172_na_tabela(driver)

        # 4. identificar o novo card
        card_id = get_last_item_card_id(driver)

        # 5. preencher valor e apelido via JS setter
        setar_valor_e_apelido_no_card(driver, card_id, valor_fmt, apelido)

        # 6. salvar o item
        salvar_item_card(driver, card_id, valor_fmt)

        # 7. evidência
        shot(driver, f"proc_{num_processo}_item_{card_id}_{apelido}.png")

    print(f"✅ {len(linhas)} itens cadastrados para o processo {num_processo}.")


# ========== 3) LOCALIZAR E CASAR NO DC ==========

@retry_once
def localizar_e_casar_no_dc(driver, bucket: Tuple[str, List[Dict]]):
    """
    Envia itens ao DC e casa cada item pelo apelido + valor.
    """
    num_processo, linhas = bucket
    print(f"📦 Enviando itens do processo {num_processo} ao DC...")

    # abrir carrinho e enviar
    wclick(driver, S.CARRINHO_BTN, TIMEOUT)
    wclick(driver, S.DC_ADD_BTN, TIMEOUT)
    if is_visible(driver, S.DC_CONFIRMAR_BTN, 2):
        wclick(driver, S.DC_CONFIRMAR_BTN, TIMEOUT)
    wait_dom_stable(driver)
    shot(driver, f"proc_{num_processo}_dc_entrada.png")

    assert is_visible(driver, S.DC_FIELDSET, TIMEOUT), "❌ Fieldset DC não visível!"

    print("🔎 Localizando e casando cada item no DC...")
    for cfg in linhas:
        valor_fmt = cur4(cfg.get("valor", "0"))
        apelido = apelido_from_cfg(cfg)

        # localizar card no DC
        card_root = find_dc_card_by_value_and_apelido(driver, valor_fmt, apelido, scope_css=S.DC_FIELDSET)
        if card_root is None:
            raise RuntimeError(f"Item não encontrado no DC (apelido='{apelido}', valor='{valor_fmt}').")

        # aqui virá o complemento (fornecedor, locais etc.)
        complementar_dc(driver, card_root, cfg)

        shot(driver, f"proc_{num_processo}_dc_casado_{apelido}.png")

    print(f"✅ Itens do processo {num_processo} casados com sucesso no DC.")


# ---------- AUXILIARES ESPECÍFICOS DO STEP ----------

def selecionar_21172_na_tabela(driver):
    """
    Na tabela do catálogo, encontra linha com 'Treinamento Qualificação Profissional' e clica em Adicionar.
    """
    assert is_visible(driver, S.CATALOGO_TABELA, TIMEOUT), "Tabela catálogo não visível!"
    rows = find_rows_by_text(driver, S.CATALOGO_TABELA, S.CATALOGO_LINHA_DESCR, "Treinamento Qualificação Profissional")
    if not rows:
        raise RuntimeError("Linha 21172 não encontrada no catálogo!")
    wclick(driver, S.CATALOGO_LINHA_BTN_ADICIONAR, TIMEOUT)
    wait_dom_stable(driver)

def setar_valor_e_apelido_no_card(driver, card_id: str, valor_fmt: str, apelido: str):
    """Preenche valor e apelido com JS + eventos (idempotente)."""
    valor_input = S.valor_input(card_id)
    valor_espelho = S.valor_espelho(card_id)
    js_set_value(driver, valor_input, valor_fmt, fire=True)
    wait_text(driver, valor_espelho, f"R$ {valor_fmt}", TIMEOUT)
    js_set_value(driver, S.apelido_input(card_id), apelido, fire=True)

def salvar_item_card(driver, card_id: str, valor_fmt: str):
    """Salva o card e valida pós-salvamento."""
    wclick(driver, S.salvar_item(card_id), TIMEOUT)
    wait_dom_stable(driver)
    wait_text(driver, S.valor_espelho(card_id), f"R$ {valor_fmt}", TIMEOUT)

def complementar_dc(driver, card_root, cfg: Dict):
    """
    Hook para preencher campos complementares no DC.
    Exemplo: fornecedor, local de entrega, NBS, etc.
    """
    # implementar depois com seus seletores DC
    pass


# ========== FUNÇÃO ORQUESTRADORA PRINCIPAL ==========

def executar_step_b(driver, cfg_list: List[Dict]):
    """
    Orquestra Step B completo (Itens + DC) com apelido ativo.
    """
    buckets = abrir_itens_e_bucketizar(driver, cfg_list)
    for bucket in buckets:
        cadastrar_itens_21172(driver, bucket)
        localizar_e_casar_no_dc(driver, bucket)
    print("🎯 Step B concluído com sucesso para todos os processos.")

def run(driver):
    """
    Wrapper chamado pelo main.py.
    Carrega a planilha e executa o Step B completo (Itens + DC).
    """
    cfg_list = load_all_cfgs()
    executar_step_b(driver, cfg_list)
