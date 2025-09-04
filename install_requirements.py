import subprocess
import sys

# lista de bibliotecas que seu projeto usa
packages = [
    "pandas",
    "selenium",
    "webdriver-manager"
]

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if __name__ == "__main__":
    for package in packages:
        print(f"📦 Instalando {package} ...")
        install(package)
    print("\n✅ Todas as bibliotecas foram instaladas com sucesso!")
