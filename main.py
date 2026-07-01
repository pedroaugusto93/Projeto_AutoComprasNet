# main.py
"""
Ponto de entrada do AutoComprasNet.

Conecta no Chrome (debug), navega até a tela de execução, carrega a planilha uma
única vez e executa as abas em sequência. Ao final, imprime um relatório do que
foi executado e do que falhou.
"""
#  & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\ChromeDebugProfile"   

import time

from selenium.webdriver.support.ui import WebDriverWait

import config
import page_dados_basicos
import page_itens
from driver import get_driver
from helpers import carregar_itens
from logger import get_logger

log = get_logger(__name__)

# Abas executadas, na ordem. Documentos/Empenhos entram aqui quando prontas.
#   (rótulo, função que recebe (driver, itens))
# Dados Básicos usa a 1ª linha como cabeçalho da contratação (fluxo single-process
# por ora; multi-process = um cabeçalho por bucket, evolução futura).
ETAPAS = [
    ("Dados Básicos", lambda d, itens: page_dados_basicos.run(d, itens[0])),
    ("Itens + DC", lambda d, itens: page_itens.executar(d, itens)),
    # ("Documentos", lambda d, itens: page_documentos.executar(d, itens)),
    # ("Empenhos",   lambda d, itens: page_empenhos.executar(d, itens)),
]


def _navegar(driver) -> None:
    """Vai para a URL alvo e espera a tela de execução carregar."""
    driver.switch_to.window(driver.window_handles[0])
    driver.get(config.TARGET_URL)
    WebDriverWait(driver, config.TIMEOUT).until(
        lambda d: config.URL_READY_TOKEN in d.current_url
    )
    log.info("Tela de execução carregada.")


def main() -> int:
    config.garantir_diretorios()
    inicio = time.time()
    driver = get_driver()
    _navegar(driver)

    itens = carregar_itens()
    if not itens:
        log.error("Planilha vazia — nada a processar.")
        return 1

    resultados = []
    for rotulo, executar in ETAPAS:
        log.info("▶ Etapa: %s", rotulo)
        try:
            executar(driver, itens)
            resultados.append((rotulo, "OK", ""))
        except Exception as exc:
            log.exception("Falha na etapa '%s'", rotulo)
            resultados.append((rotulo, "ERRO", str(exc)))
            break  # aborta o fluxo na primeira etapa que falhar

    _relatorio(resultados, time.time() - inicio)
    return 0 if all(status == "OK" for _, status, _ in resultados) else 1


def _relatorio(resultados, segundos: float) -> None:
    """Imprime um resumo final da execução."""
    log.info("=" * 52)
    log.info("RELATÓRIO DE EXECUÇÃO")
    for rotulo, status, detalhe in resultados:
        marca = "✅" if status == "OK" else "❌"
        sufixo = f" — {detalhe}" if detalhe else ""
        log.info("  %s %-16s %s%s", marca, rotulo, status, sufixo)
    log.info("Tempo total: %.1fs", segundos)
    log.info("Evidências/Logs: %s", config.LOGS_DIR)
    log.info("=" * 52)


if __name__ == "__main__":
    raise SystemExit(main())
