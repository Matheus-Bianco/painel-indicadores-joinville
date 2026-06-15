import pandas as pd
import numpy as np
import json, os, glob, time

BASE = r"c:\Users\mathe\OneDrive\Desktop\Trabalhos\02. Joinville\25. Painel de Indicadores Abertos Joinville\04. Produto 4_Indicadores Educacionais"
OUT_DIR = os.path.join(BASE, "painel", "dados")

def test_etl():
    print("Testing ETL script writing...")
