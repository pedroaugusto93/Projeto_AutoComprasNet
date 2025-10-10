# helpers.py
# config.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd

DEBUG_PORT = 9222  # mesma porta usada ao abrir o Chrome

def get_driver():
    """Conecta ao Chrome já aberto em modo depurador."""
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

PLANILHA_PATH = r"C:\Users\pedro.naia\OneDrive - MPRJ\Arquivo\Documentos\Projeto_AutoSIGIFIS\cadastro.xlsx"
SHEET_NAME = "Sheet1"

def load_data():
    """Carrega a planilha inteira como DataFrame"""
    return pd.read_excel(PLANILHA_PATH, sheet_name=SHEET_NAME)

def load_all_cfgs(path=PLANILHA_PATH, sheet=SHEET_NAME):
    """Lê a aba `sheet` e retorna lista de dicionários (um por linha)."""
    df = pd.read_excel(path, sheet_name=sheet, dtype=str).fillna("")
    cfg_list = [row.to_dict() for _, row in df.iterrows()]

    for cfg in cfg_list:
        # Campos do projeto (planilha)
        #cfg.setdefault('titulo', "")
        #cfg.setdefault('justificativa', "")
        #cfg.setdefault('num_processo', "")
        cfg.setdefault('tipo_contratacao', "")
        cfg.setdefault('fundamento_legal', "")
        cfg.setdefault('categoria', "")
        cfg.setdefault('moeda_compra', "")
        cfg.setdefault('compra_srp', "")
        #cfg.setdefault('descricao_objeto', "")
        cfg.setdefault('info_complementares', "")
        cfg.setdefault('item', "")
        cfg.setdefault('fornecedor_id', "")
        cfg.setdefault('fornecedor_nome', "")
        cfg.setdefault('valor', "")
        cfg.setdefault('quantidade', "")
        cfg.setdefault('valor_total', "")
        cfg.setdefault('resp_cpf', "")
        cfg.setdefault('resp_nome', "")
        cfg.setdefault('resp_email', "")
        cfg.setdefault('resp_cargo', "")
        cfg.setdefault('resp_despacho', "")
        cfg.setdefault('autoridade_cpf', "")
        cfg.setdefault('autoridade_nome', "")
        cfg.setdefault('autoridade_email', "")
        cfg.setdefault('autoridade_cargo', "")
        cfg.setdefault('autoridade_despacho', "")
        


def titulo():
    return 'Pós-graduação Lato Sensu “Crianças, Adolescentes e Famílias"'

def justificativa():
    return 'MPRJ não é órgão SISG'

def data_inicial():
    return (1, 9, 2025)

def data_final():
    return (30, 9, 2025)

def descricao_objeto():
    return (
        "Contratação de instituição de ensino superior para realização do curso "
        "de pós-graduação lato sensu “Crianças, Adolescentes e Famílias, com "
        "carga horária de 360 horas/aula, a ser ministrado na cidade do Rio de "
        "Janeiro, conforme especificações e condições constantes no Termo de "
        "Referência que integra este edital."
    )
def num_processo():
    return "20.22.0001.0010000.2025-10"
