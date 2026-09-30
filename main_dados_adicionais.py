# main_dados_adicionais.py
"""
Teste isolado da aba "2. Dados adicionais da contratação".

IMPORTANTE:
- O Chrome deve estar aberto em modo debug na porta 9222.
- A contratação do PRIMEIRO processo da planilha deve estar aberta.
- Este script NÃO executa page_itens.py.
- Portanto, é seguro para testar Dados Adicionais sem recadastrar os itens.
"""

import time

import config
import page_dados_adicionais

from driver import get_driver
from helpers import carregar_itens
from logger import get_logger


log = get_logger(__name__)


def main() -> int:
    config.garantir_diretorios()
    inicio = time.time()

    driver = get_driver()
    driver.switch_to.window(
        driver.window_handles[0]
    )

    log.info(
        "Tela atual preservada."
    )
    log.info(
        "URL atual: %s",
        driver.current_url,
    )

    itens = carregar_itens()

    if not itens:
        log.error(
            "Planilha vazia — nada a processar."
        )
        return 1

    log.info(
        "▶ TESTE ISOLADO: Dados adicionais"
    )

    try:
        page_dados_adicionais.executar(
            driver,
            itens,
        )

    except Exception as exc:
        log.exception(
            "Falha na etapa 'Dados adicionais'"
        )
        log.info(
            "Tempo total: %.1fs",
            time.time() - inicio,
        )
        return 1

    log.info(
        "✓ Dados adicionais concluídos."
    )
    log.info(
        "Tempo total: %.1fs",
        time.time() - inicio,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
