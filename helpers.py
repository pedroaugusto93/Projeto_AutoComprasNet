# helpers.py
import pandas as pd

PLANILHA_PATH = r"C:\Users\pedro.naia\OneDrive - MPRJ\Arquivo\Documentos\Projeto_AutoSIGIFIS\cadastro.xlsx"
SHEET_NAME = "Sheet1"

# carrega a aba inteira como DataFrame
def load_data():
    return pd.read_excel(PLANILHA_PATH, sheet_name=SHEET_NAME)

# atalhos para acessar colunas específicas
def get_processo(df):         return df["PROCESSO"]
def get_valor(df):            return df["VALOR"]
def get_cnpj(df):             return df["CNPJ_FORNECEDOR"]
def get_nome_fornecedor(df):  return df["NOME_FORNECEDOR"]
def get_prazo(df):            return df["PRAZO_EXECUCAO"]
def get_ano_empenho(df):      return df["ANO_EMPENHO"]
def get_data_empenho(df):     return df["DATA_EMPENHO"]
def get_num_empenho(df):      return df["NUM_EMPENHO"]
def get_nome_curso(df):       return df["NOME_CURSO"]
def get_objeto(df):           return df["OBJETO"]
def get_num_item(df):         return df["NUM_ITEM"]
def get_file_path(df):        return df["FILE_PATH"]
def get_cpf_ordenador(df):    return df["CPF_ORDENADOR"]
def get_data_ato(df):         return df["DATA_ATO"]


