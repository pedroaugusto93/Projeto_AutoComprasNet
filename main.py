# main_teste_itens.py
"""
Teste isolado da etapa "Itens + DC".

IMPORTANTE:
- O Chrome deve estar aberto em modo debug na porta 9222.
- A contratação deve estar atualmente aberta na tela de edição.
- Este script NÃO executa Dados Básicos.
- Este script NÃO navega para a tela inicial.
- Ele usa exatamente a página que já está aberta e inicia em "3. Itens/Grupos".
"""

import time

import config
import page_itens

from driver import get_driver
from helpers import carregar_itens
from logger import get_logger


log = get_logger(__name__)


def main() -> int:
    config.garantir_diretorios()

    inicio = time.time()

    # Conecta no Chrome já aberto em modo debug.
    driver = get_driver()

    # Usa a primeira janela existente, SEM navegar para outra URL.
    driver.switch_to.window(driver.window_handles[0])

    log.info("Tela atual preservada.")
    log.info("URL atual: %s", driver.current_url)

    # Carrega os itens da planilha.
    itens = carregar_itens()

    if not itens:
        log.error("Planilha vazia — nada a processar.")
        return 1

    log.info("▶ TESTE ISOLADO: Itens + DC")

    try:
        page_itens.executar(driver, itens)

    except Exception as exc:
        log.exception("Falha na etapa 'Itens + DC'")
        _relatorio(
            status="ERRO",
            detalhe=str(exc),
            segundos=time.time() - inicio,
        )
        return 1

    _relatorio(
        status="OK",
        detalhe="",
        segundos=time.time() - inicio,
    )

    return 0


def _relatorio(
    status: str,
    detalhe: str,
    segundos: float,
) -> None:
    log.info("=" * 52)
    log.info("RELATÓRIO DE EXECUÇÃO — TESTE ITENS")

    marca = "✅" if status == "OK" else "❌"
    sufixo = f" — {detalhe}" if detalhe else ""

    log.info(
        "  %s %-16s %s%s",
        marca,
        "Itens + DC",
        status,
        sufixo,
    )

    log.info(
        "Tempo total: %.1fs",
        segundos,
    )

    log.info(
        "Evidências/Logs: %s",
        config.LOGS_DIR,
    )

    log.info("=" * 52)


if __name__ == "__main__":
    raise SystemExit(main())
