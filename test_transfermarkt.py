import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random
import os

print("=" * 80)
print("SCRAPER TRANSFERMARKT - DEBUG")
print("=" * 80)

# =====================================================
# CONFIG
# =====================================================

URL_BASE = "https://www.transfermarkt.co"

URL_LIGA = (
    f"{URL_BASE}/liga-dimayor-apertura/startseite/wettbewerb/COL1"
)

HEADERS = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9"
}

os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

# =====================================================
# OBTENER EQUIPOS
# =====================================================

print("\nConsultando liga...\n")

response = requests.get(
    URL_LIGA,
    headers=HEADERS
)

print("STATUS:", response.status_code)

if response.status_code != 200:
    raise Exception(
        f"Error consultando liga: {response.status_code}"
    )

soup = BeautifulSoup(
    response.text,
    "html.parser"
)

tabla = soup.find(
    "table",
    class_="items"
)

if tabla is None:
    raise Exception(
        "No encontré la tabla de equipos."
    )

filas = tabla.find("tbody").find_all("tr")

equipos = []

for fila in filas:

    try:

        link_tag = fila.find(
            "td",
            class_="hauptlink"
        )

        if link_tag is None:
            continue

        a = link_tag.find("a")

        if a is None:
            continue

        nombre = a.text.strip()

        href = a.get("href")

        equipos.append(
            {
                "equipo": nombre,
                "url": f"{URL_BASE}{href}"
            }
        )

    except Exception as e:

        print(
            "Error leyendo fila:",
            e
        )

print(
    f"\nEquipos encontrados: {len(equipos)}"
)

print("\nPrimeros 5 equipos:\n")

for x in equipos[:5]:
    print(x)

# =====================================================
# EXTRAER JUGADORES
# =====================================================

jugadores = []

for i, equipo in enumerate(equipos):

    print(
        f"\n[{i+1}/{len(equipos)}] "
        f"{equipo['equipo']}"
    )

    try:

        time.sleep(
            random.uniform(2, 4)
        )

        r = requests.get(
            equipo["url"],
            headers=HEADERS
        )

        print(
            "STATUS:",
            r.status_code
        )

        print(
            "URL:",
            r.url
        )

        if r.status_code != 200:
            continue

        soup_eq = BeautifulSoup(
            r.text,
            "html.parser"
        )

        tablas = soup_eq.find_all(
            "table"
        )

        print(
            "Tablas encontradas:",
            len(tablas)
        )

        tabla_jugadores = soup_eq.find(
            "table",
            class_="items"
        )

        if tabla_jugadores is None:

            print(
                "No encontré tabla items."
            )

            continue

        cuerpo = tabla_jugadores.find(
            "tbody"
        )

        if cuerpo is None:

            print(
                "No encontré tbody."
            )

            continue

        filas_jugadores = cuerpo.find_all(
            "tr",
            recursive=False
        )

        print(
            "Filas encontradas:",
            len(filas_jugadores)
        )

        contador = 0

        for fila in filas_jugadores:

            if (
                "bg_blau_20"
                in fila.get("class", [])
            ):
                continue

            nombre_tag = fila.find(
                "td",
                class_="hauptlink"
            )

            if nombre_tag is None:
                continue

            nombre_jugador = (
                nombre_tag.text.strip()
            )

            valor = 0.0

            try:

                columnas_valor = fila.find_all(
                    "td",
                    class_="rechts"
                )

                if len(columnas_valor) > 0:

                    valor_raw = (
                        columnas_valor[-1]
                        .text
                        .strip()
                    )

                    match = re.search(
                        r"[\d\,]+",
                        valor_raw
                    )

                    if match:

                        numero = float(
                            match.group()
                            .replace(",", ".")
                        )

                        if (
                            "mill"
                            in valor_raw.lower()
                        ):
                            valor = numero

                        elif (
                            "mil"
                            in valor_raw.lower()
                        ):
                            valor = numero / 1000

            except:
                pass

            jugadores.append(
                {
                    "equipo": equipo["equipo"],
                    "jugador": nombre_jugador,
                    "valor_millones_eur": valor
                }
            )

            contador += 1

        print(
            "Jugadores encontrados:",
            contador
        )

    except Exception as e:

        print(
            f"ERROR: {e}"
        )

# =====================================================
# DATAFRAME
# =====================================================

df = pd.DataFrame(
    jugadores
)

print("\n")
print("=" * 80)
print("RESULTADO FINAL")
print("=" * 80)

print(
    "Registros:",
    len(df)
)

print(
    "Equipos:",
    df["equipo"].nunique()
    if len(df) > 0 else 0
)

print("\nPrimeras filas:\n")

print(df.head())

# =====================================================
# GUARDAR JUGADORES
# =====================================================

archivo_jugadores = (
    "data/raw/jugadores.csv"
)

df.to_csv(
    archivo_jugadores,
    index=False,
    encoding="utf-8-sig"
)

print(
    f"\nArchivo guardado: "
    f"{archivo_jugadores}"
)

# =====================================================
# NOMINAS
# =====================================================

if len(df) > 0:

    nominas = (
        df.groupby("equipo")
        ["valor_millones_eur"]
        .sum()
        .reset_index()
    )

    nominas.columns = [
        "equipo",
        "valor_nomina_millones_eur"
    ]

    nominas = nominas.sort_values(
        "valor_nomina_millones_eur",
        ascending=False
    )

    print("\nTODAS LAS NÓMINAS:\n")

    print(
        nominas.to_string(index=False)
    )

    archivo_nominas = (
        "data/processed/nominas.csv"
    )

    nominas.to_csv(
        archivo_nominas,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"\nArchivo guardado: "
        f"{archivo_nominas}"
    )

print("\nFIN.")