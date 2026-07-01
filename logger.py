# logger.py
"""
Logging estruturado do projeto.

Substitui os prints espalhados por um logger único que escreve no console e
num arquivo em logs/. Mantém um tom amigável (emojis opcionais) sem perder
timestamp, nível e origem — o que faltava no AutoSIGFIS e gerava ruído.

Uso:
    from logger import get_logger
    log = get_logger(__name__)
    log.info("Mensagem")
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

import config

_CONFIGURADO = False


def _configurar_raiz() -> None:
    """Configura os handlers uma única vez (console + arquivo rotativo)."""
    global _CONFIGURADO
    if _CONFIGURADO:
        return

    config.garantir_diretorios()

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(fmt)

    arquivo = RotatingFileHandler(
        config.LOGS_DIR / "comprasnet.log",
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    arquivo.setFormatter(fmt)

    raiz = logging.getLogger("comprasnet")
    raiz.setLevel(logging.INFO)
    raiz.handlers.clear()
    raiz.addHandler(console)
    raiz.addHandler(arquivo)
    raiz.propagate = False

    _CONFIGURADO = True


def get_logger(nome: str) -> logging.Logger:
    """Devolve um logger filho de 'comprasnet' já configurado."""
    _configurar_raiz()
    # Normaliza "__main__"/"page_itens" para comprasnet.<nome>
    sufixo = nome.split(".")[-1] if nome != "__main__" else "main"
    return logging.getLogger(f"comprasnet.{sufixo}")
