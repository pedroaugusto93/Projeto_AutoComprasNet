# page_documentos.py
"""
Aba "Documentos" (antigo step_c — ainda não implementado).

Esqueleto no mesmo padrão dos demais page modules: recebe o driver e a lista de
itens, registra o progresso via logger e devolve controle ao main. Implementar o
fluxo de anexos quando os seletores da aba estiverem mapeados em selectors.S.
"""

from __future__ import annotations

from typing import List

import config
from logger import get_logger
from models import ItemContratacao

log = get_logger(__name__)


def executar(driver, itens: List[ItemContratacao]) -> None:
    """Executa a aba Documentos (a implementar)."""
    log.warning("Aba Documentos ainda não implementada — etapa pulada.")


def run(driver) -> None:
    """Wrapper chamado pelo main.py."""
    from helpers import carregar_itens

    executar(driver, carregar_itens())
