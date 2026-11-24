from time import sleep

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# [CSV - PASSO 1] Importar a funções

import csv
import os
import re
from datetime import datetime

PESQUISA = "macbook pro"
URL_OLX = "https://www.olx.com.br/"
HEADLESS = False
MAX_RESULTADOS = 10 #NÃO COLOQUE UM VALOR MUITO ALTO!!!!


def abrir_navegador():
    opcoes = webdriver.ChromeOptions()
    if HEADLESS:
        opcoes.add_argument("--headless=new")
    opcoes.add_argument("--window-size=1366,900")
    return webdriver.Chrome(options=opcoes)


def pesquisar(driver, termo):
    driver.get(URL_OLX)
    wait = WebDriverWait(driver, 15)

    campo = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, 'input[name="search-input"]')))
    campo.clear()
    campo.send_keys(termo)
    sleep(1)
    campo.send_keys(Keys.ENTER)

    try:
        WebDriverWait(driver, 5).until(EC.url_contains("q="))
    except TimeoutException:
        driver.find_element(By.CSS_SELECTOR, 'form button[type="submit"]').click()
        wait.until(EC.url_contains("q="))

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "section.olx-adcard")))


def ler_resultados(driver, limite):
    anuncios = []
    for card in driver.find_elements(By.CSS_SELECTOR, "section.olx-adcard")[:limite]:
        def texto(seletor):
            achados = card.find_elements(By.CSS_SELECTOR, seletor)
            return achados[0].text.strip() if achados else ""

        link = card.find_elements(By.CSS_SELECTOR, "a[data-testid=adcard-link]")
        anuncios.append({
            "titulo": texto(".olx-adcard__title"),
            "preco": texto(".olx-adcard__price"),
            "local": texto(".olx-adcard__location"),
            "link": link[0].get_attribute("href") if link else "",
        })
    return anuncios


def recusar_cookies(driver):
    botoes = driver.find_elements(By.ID, "adopt-reject-all-button")
    if botoes:
        driver.execute_script("arguments[0].click();", botoes[0])
        sleep(1)


def abrir_primeiro_anuncio(driver):
    wait = WebDriverWait(driver, 15)
    recusar_cookies(driver)

    abas_antes = len(driver.window_handles)
    primeiro = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "section.olx-adcard a[data-testid=adcard-link]")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", primeiro)
    primeiro.click()

    wait.until(EC.number_of_windows_to_be(abas_antes + 1))
    driver.switch_to.window(driver.window_handles[-1])

    preco = wait.until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, ".advc-price-box"))).text.splitlines()[0]
    titulo = driver.title.split(" - ")[0]
    return {"titulo": titulo, "preco": preco, "link": driver.current_url}


# [CSV - PASSO 2] Criar função de gerar nome do arquivo

def gerar_nome_arquivo(nome_base):
    nome_limpo = re.sub(r"[^a-z0-9]+", "_", nome_base.lower()).strip("_")
    data_hora = datenow().strftime("%Y%m%d_%H%M%S")
    return f"{nome_limpo}_{data_hora}.csv"

# [CSV - PASSO 3] Criar função para salvar o csv

def salvar_csv(dados, nome_base="resultados", pasta="resultados", separador=";"):
    if not dados:
        print("Nada para salvar.")
        return None

    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, gerar_nome_arquivo(nome_base))

    colunas = list(dict.fromkeys(chave for linha in dados for chave in linha))

    with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, delimiter=separador)
        escritor.writeheader()
        escritor.writerows(dados)

    return caminho

def main():
    driver = abrir_navegador()
    try:
        pesquisar(driver, PESQUISA)
        print(f'Busca: "{PESQUISA}"')
        print(f"Página: {driver.current_url}\n")

        anuncios = ler_resultados(driver, MAX_RESULTADOS)
        assert anuncios, "nenhum anúncio encontrado na página de resultados"

        for i, a in enumerate(anuncios, 1):
            print(f"{i:2}. {a['titulo']}")
            print(f"    {a['preco']}  |  {a['local']}")
            print(f"    {a['link']}")
        print(f"\nOK: {len(anuncios)} anúncios lidos.")

        # [CSV - PASSO 4] Salvar a lista de anúncios em CSV, usando a pesquisa como nome do arquivo
        caminho = salvar_csv(anuncios, nome_base=PESQUISA)
        print(f"CSV salvo em: {caminho}")

        anuncio = abrir_primeiro_anuncio(driver)
        print("\nPrimeiro anúncio aberto:")
        print(f"    {anuncio['titulo']}  |  {anuncio['preco']}")
        print(f"    {anuncio['link']}")

        # [CSV - PASSO 5] Salvar também o anúncio aberto, em outro arquivo (a função aceita qualquer lista de dicionários)
        caminho = salvar_csv([anuncio], nome_base=PESQUISA + " primeiro anuncio")
        print(f"CSV salvo em: {caminho}")

        if not HEADLESS:
            input("\nENTER para fechar o navegador...")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
