# page_empenhos.py
"""
Aba "Empenhos" (antigo step_d — ainda não implementado).

Esqueleto no mesmo padrão dos demais page modules. Implementar quando os
seletores da aba estiverem mapeados em selectors.S.
"""

from __future__ import annotations

from typing import List

import config
from logger import get_logger
from models import ItemContratacao

log = get_logger(__name__)


def executar(driver, itens: List[ItemContratacao]) -> None:
    """Executa a aba Empenhos (a implementar)."""
    log.warning("Aba Empenhos ainda não implementada — etapa pulada.")


def run(driver) -> None:
    """Wrapper chamado pelo main.py."""
    from helpers import carregar_itens

    executar(driver, carregar_itens())
