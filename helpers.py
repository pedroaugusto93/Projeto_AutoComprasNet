# helpers.py
"""
Acesso a dados (planilha).

Responsabilidade única: ler cadastro.xlsx e devolver uma lista de
`ItemContratacao`. Tudo que não era disso (criação de driver, dados de negócio
fixos, caminhos hardcoded) saiu daqui para driver.py / config.py / models.py.
"""

from __future__ import annotations

from typing import List

import pandas as pd

import config
from logger import get_logger
from models import ItemContratacao

log = get_logger(__name__)


def carregar_itens() -> List[ItemContratacao]:
    """Lê a planilha e devolve uma lista de itens (um por linha)."""
    caminho = config.PLANILHA_PATH
    log.info("Lendo planilha: %s | aba: %s", caminho, config.SHEET_NAME)

    if not caminho.exists():
        raise FileNotFoundError(f"Planilha não encontrada em: {caminho}")

    df = pd.read_excel(caminho, sheet_name=config.SHEET_NAME, dtype=str).fillna("")
    if df.empty:
        log.warning("Planilha lida, mas sem linhas.")
        return []

    itens = [ItemContratacao.from_row(row.to_dict()) for _, row in df.iterrows()]
    log.info("Linhas carregadas: %d", len(itens))
    return itens
