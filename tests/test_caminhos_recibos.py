"""Testes isolados dos caminhos e recibos; não acessam o ComprasNet."""
import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from openpyxl import Workbook

import config
import main
import page_publicacao
import pncp_status
from models import ItemContratacao


class TesteCaminhos(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="PNCP testes ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.planilha = self.base / "Controle Acadêmico.xlsx"
        self.recibos = self.base / "Recibos Compartilhados"
        self.recibos.mkdir()

        wb = Workbook()
        ws = wb.active
        ws.title = config.SHEET_NAME
        ws.append(["PROCESSO", "NOME_FORNECEDOR", "PNCP_PERC_Conclusao"])
        ws.append(["20.22.0001.0063479.2026-64", "Fornecedor Exemplo", "100%"])
        ws.append(["20.22.0001.0063480.2026-65", "Fornecedor Exemplo", ""])
        wb.save(self.planilha)
        wb.close()

        config.PLANILHA_PATH = None
        config.RECIBOS_DIR = None
        self.addCleanup(self._limpar_configuracao)

    @staticmethod
    def _limpar_configuracao():
        config.PLANILHA_PATH = None
        config.RECIBOS_DIR = None

    def test_dois_inputs_entre_aspas_na_ordem(self):
        entradas = [f' "{self.planilha}" ', f' "{self.recibos}" ']
        prompts = []
        def ler(mensagem):
            prompts.append(mensagem)
            return entradas.pop(0)

        with patch("builtins.input", side_effect=ler):
            config.solicitar_caminhos()

        self.assertEqual(config.caminho_planilha(), self.planilha)
        self.assertEqual(config.pasta_recibos(), self.recibos)
        self.assertEqual(
            prompts,
            [
                "Informe o caminho completo da planilha de cadastro: ",
                "Informe o caminho da pasta onde os recibos serão salvos: ",
            ],
        )

    def test_repete_apenas_input_incorreto(self):
        entradas = [
            '"arquivo-inexistente.xlsx"',
            f'"{self.planilha}"',
            '"pasta-inexistente"',
            f'"{self.recibos}"',
        ]
        prompts = []
        def ler(mensagem):
            prompts.append(mensagem)
            return entradas.pop(0)

        with patch("builtins.input", side_effect=ler), patch("builtins.print"):
            config.solicitar_caminhos()

        self.assertEqual(len(prompts), 4)
        self.assertEqual(prompts[0], prompts[1])
        self.assertEqual(prompts[2], prompts[3])
        self.assertEqual(config.caminho_planilha(), self.planilha)
        self.assertEqual(config.pasta_recibos(), self.recibos)

    def test_rejeita_formato_corrompido_e_pasta_nao_gravavel(self):
        invalida = self.base / "Corrompida.xlsx"
        invalida.write_text("não é uma planilha", encoding="utf-8")
        with self.assertRaises(ValueError):
            config._validar_planilha(invalida)
        with self.assertRaises(ValueError):
            config._validar_pasta_recibos(self.base / "inexistente")

    def test_nao_usa_caminho_padrao_antes_da_inicializacao(self):
        with self.assertRaises(RuntimeError):
            config.caminho_planilha()
        with self.assertRaises(RuntimeError):
            config.pasta_recibos()

    def test_status_compartilha_a_mesma_planilha_e_bloqueia_100(self):
        config.PLANILHA_PATH = self.planilha
        self.assertEqual(
            pncp_status.percentual_atual_processo_planilha(
                "20.22.0001.0063479.2026-64"
            ),
            100,
        )
        self.assertIsNone(
            pncp_status.percentual_atual_processo_planilha(
                "20.22.0001.0063480.2026-65"
            )
        )

    def test_orquestrador_ignora_concluidos_sem_alterar_fluxo(self):
        driver = MagicMock()
        driver.current_url = "https://exemplo.invalid/"
        driver.window_handles = ["principal"]
        with (
            patch("builtins.input", side_effect=[f'"{self.planilha}"', f'"{self.recibos}"']),
            patch.object(main, "get_driver", return_value=driver),
            patch.object(main, "executar_processo") as executar,
        ):
            resultado = main.main()
        self.assertEqual(resultado, 0)
        executar.assert_called_once()
        self.assertEqual(
            executar.call_args.args[1],
            "20.22.0001.0063480.2026-65",
        )


class TesteRecibos(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="PNCP recibos ")
        self.addCleanup(self.temp.cleanup)
        self.pasta = Path(self.temp.name)
        config.RECIBOS_DIR = self.pasta
        self.addCleanup(setattr, config, "RECIBOS_DIR", None)
        self.processo = "20.22.0001.0063479.2026-64"
        self.fornecedor = "Empresa Exemplo Ltda"

    def test_nome_padrao_e_coexistencia_com_tce(self):
        tce = self.pasta / f"TCE - {self.processo} - {self.fornecedor}.pdf"
        tce.write_bytes(b"%PDF-TCE")
        destino = page_publicacao._caminho_recibo(self.processo, self.fornecedor)
        self.assertEqual(
            destino.name,
            f"PNCP - {self.processo} - {self.fornecedor}.pdf",
        )
        driver = MagicMock()
        driver.execute_cdp_cmd.return_value = {
            "data": base64.b64encode(b"%PDF-PNCP").decode("ascii")
        }
        page_publicacao._salvar_pdf_recibo(driver, destino)
        self.assertEqual(tce.read_bytes(), b"%PDF-TCE")
        self.assertEqual(destino.read_bytes(), b"%PDF-PNCP")

    def test_caracteres_invalidos_substituidos_sem_remover_acentos(self):
        destino = page_publicacao._caminho_recibo(
            self.processo, 'Razão/Ação: Comércio? Ltda.'
        )
        self.assertEqual(
            destino.name,
            f"PNCP - {self.processo} - Razão-Ação- Comércio- Ltda.pdf",
        )

    def test_salvar_nao_sobrescreve_existente(self):
        destino = page_publicacao._caminho_recibo(self.processo, self.fornecedor)
        destino.write_bytes(b"%PDF-anterior")
        driver = MagicMock()
        driver.execute_cdp_cmd.return_value = {
            "data": base64.b64encode(b"%PDF-novo").decode("ascii")
        }
        with self.assertRaises(FileExistsError):
            page_publicacao._salvar_pdf_recibo(driver, destino)
        self.assertEqual(destino.read_bytes(), b"%PDF-anterior")

    def test_bloqueia_publicacao_sem_fornecedor_antes_do_clique(self):
        driver = MagicMock()
        itens = [ItemContratacao(PROCESSO=self.processo, NOME_FORNECEDOR="")]
        with self.assertRaisesRegex(RuntimeError, "Fornecedor não identificado"):
            page_publicacao.executar_processo(driver, itens)
        driver.find_elements.assert_not_called()

    def test_bloqueia_publicacao_com_recibo_existente_antes_do_clique(self):
        destino = page_publicacao._caminho_recibo(self.processo, self.fornecedor)
        destino.write_bytes(b"%PDF-anterior")
        driver = MagicMock()
        itens = [
            ItemContratacao(PROCESSO=self.processo, NOME_FORNECEDOR=self.fornecedor)
        ]
        with self.assertRaises(FileExistsError):
            page_publicacao.executar_processo(driver, itens)
        driver.find_elements.assert_not_called()

    def test_bloqueia_nome_ambiguo_antes_do_clique(self):
        itens = [
            ItemContratacao(PROCESSO=self.processo, NOME_FORNECEDOR="Empresa A"),
            ItemContratacao(PROCESSO=self.processo, NOME_FORNECEDOR="Empresa B"),
        ]
        driver = MagicMock()
        with self.assertRaisesRegex(RuntimeError, "fornecedores diferentes"):
            page_publicacao.executar_processo(driver, itens)
        driver.find_elements.assert_not_called()


if __name__ == "__main__":
    unittest.main()
