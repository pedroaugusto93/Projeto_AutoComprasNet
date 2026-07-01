# config.py
"""
Configuração centralizada do Projeto AutoComprasNet.

Caminhos, navegador, tempos, URLs e — importante — as CONSTANTES de negócio
(as poucas coisas que não variam por linha da planilha). Todo o resto vem de
cadastro.xlsx, a mesma planilha do AutoSIGFIS (ver models.ItemContratacao).
"""

from __future__ import annotations

import os
from pathlib import Path

# --------------------------------------------------------------------------- #
# CAMINHOS
# --------------------------------------------------------------------------- #
BASE_DIR = Path(__file__).resolve().parent          # .../Projeto_AutoComprasNet/src
PROJECT_DIR = BASE_DIR.parent

# Mesma planilha do AutoSIGFIS. Pode ser apontada por env var.
PLANILHA_PATH = Path(os.getenv("COMPRASNET_PLANILHA", BASE_DIR / "cadastro.xlsx"))
SHEET_NAME = os.getenv("COMPRASNET_SHEET", "Sheet1")

LOGS_DIR = Path(os.getenv("COMPRASNET_LOGS", BASE_DIR / "logs"))
SHOTS_DIR = LOGS_DIR / "shots"

# --------------------------------------------------------------------------- #
# NAVEGADOR (Chrome em modo Remote Debugging)
# --------------------------------------------------------------------------- #
CHROME_DEBUG_HOST = os.getenv("CHROME_DEBUG_HOST", "127.0.0.1")
CHROME_DEBUG_PORT = int(os.getenv("CHROME_DEBUG_PORT", "9222"))

# --------------------------------------------------------------------------- #
# TEMPOS
# --------------------------------------------------------------------------- #
TIMEOUT = int(os.getenv("TIMEOUT_SECONDS", "30"))
DOM_SETTLE = float(os.getenv("DOM_SETTLE", "0.5"))

# --------------------------------------------------------------------------- #
# URLS
# --------------------------------------------------------------------------- #
TARGET_URL = os.getenv(
    "COMPRASNET_URL",
    "https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-artefatos-web/execucao",
)
URL_READY_TOKEN = "/comprasnet-artefatos-web/execucao"


# --------------------------------------------------------------------------- #
# CONSTANTES DE NEGÓCIO (não variam por linha)
# --------------------------------------------------------------------------- #
class Constantes:
    """
    As únicas coisas fixas do fluxo. TODO o resto vem da planilha.
    (Confirmadas: fundamentação jurídica, modalidade, justificativa,
    item 1, unidade/serviço = 1.)
    """

    # Aba Dados Básicos
    JUSTIFICATIVA = "MPRJ não é órgão SISG"
    CATEGORIA = "Serviços"                            # categoria sempre "Serviços"
    TIPO_CONTRATACAO = "Dispensa de licitação"        # aria-label exato do dropdown
    MODO_DISPUTA = "Não se aplica"                    # aria-label exato do dropdown
    FUNDAMENTO_LEGAL = "LEI 14.133/2021 - Art. 75 - Inciso II"

    # Fundamentação legal na árvore: LEI 14.133/2021 > Art. 75 > Inciso II.
    FUND_LEI = "LEI 14.133/2021"
    FUND_ARTIGO = "Art. 75"
    FUND_INCISO_PREFIXO = "Inciso II:"                # aria-label começa com isso

    # PCA (Plano de Contratações Anual) — rótulo montado como "PCA {ano} - {status}"
    PCA_STATUS = "Em Execução"

    # Aba Itens — o catálogo sempre busca o mesmo PDM/serviço
    CODIGO_ITEM = os.getenv("COMPRASNET_CODIGO_ITEM", "21172")
    TEXTO_SERVICO_ITEM = "Treinamento Qualificação Profissional"
    NUM_ITEM = "1"          # "item 1"
    QTD_ITEM = "1"          # "unidade serv 1" (quantidade do serviço)
    UNID_MEDIDA = "UNIDADE" # unidade de fornecimento — confirmar rótulo no ComprasNet


# Atalhos retrocompatíveis (usados por app_selectors / page_itens).
CODIGO_ITEM = Constantes.CODIGO_ITEM
TEXTO_SERVICO_ITEM = Constantes.TEXTO_SERVICO_ITEM


# --------------------------------------------------------------------------- #
# DATAS
# --------------------------------------------------------------------------- #
# As datas agora vêm da planilha:
#   • "Data de início" (campo #data-inicio-contratacao)  <- coluna DATA_INICIO
#   • "Data de término" (campo #data-fim-contratacao)    <- coluna DATA_EMPENHO
# Formato de entrada aceito: ISO ("2026-06-17 00:00:00") ou "dd/mm/aaaa".


def garantir_diretorios() -> None:
    """Cria as pastas de saída (logs/shots) se ainda não existirem."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    SHOTS_DIR.mkdir(parents=True, exist_ok=True)
