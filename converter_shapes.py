# -*- coding: utf-8 -*-
"""
Converte shapefile de municipios RS para TopoJSON otimizado.
Simplifica geometrias para reduzir tamanho (~13MB shp -> ~1-2MB topojson).
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import geopandas as gpd
import topojson as tp
import json, os

BASE = r"c:\Users\mathe\OneDrive\Desktop\Trabalhos\02. Joinville\25. Painel de Indicadores Abertos Joinville\04. Produto 4_Indicadores Educacionais"
SHP = os.path.join(BASE, "00. Bases de Dados", "06. Shapes", "RS_Municipios_2025.shp")
OUT_DIR = os.path.join(BASE, "painel", "dados")

print("Lendo shapefile...")
gdf = gpd.read_file(SHP)

# Reprojetar para WGS84 se necessario
if gdf.crs and gdf.crs.to_epsg() != 4326:
    print(f"  Reprojetando de {gdf.crs} para EPSG:4326...")
    gdf = gdf.to_crs(epsg=4326)

# Manter apenas colunas essenciais
gdf = gdf[["CD_MUN", "NM_MUN", "NM_RGI", "NM_RGINT", "AREA_KM2", "geometry"]]
gdf = gdf.rename(columns={
    "CD_MUN": "cod_mun",
    "NM_MUN": "nome",
    "NM_RGI": "regiao_imediata",
    "NM_RGINT": "regiao_intermediaria",
    "AREA_KM2": "area_km2",
})

print(f"  {len(gdf)} municipios")

# Converter para TopoJSON com simplificacao
print("Convertendo para TopoJSON (simplificando geometrias)...")
topo = tp.Topology(gdf, toposimplify=0.0001)

# Salvar
out_path = os.path.join(OUT_DIR, "rs_municipios.topojson.json")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(topo.to_json())

size_mb = os.path.getsize(out_path) / 1024 / 1024
print(f"  Salvo: {out_path}")
print(f"  Tamanho: {size_mb:.1f} MB")

# Tambem salvar GeoJSON simplificado como fallback
print("Gerando GeoJSON simplificado...")
gdf_simple = gdf.copy()
gdf_simple["geometry"] = gdf_simple["geometry"].simplify(tolerance=0.005, preserve_topology=True)

out_geojson = os.path.join(OUT_DIR, "rs_municipios.geojson")
gdf_simple.to_file(out_geojson, driver="GeoJSON")

size_geo = os.path.getsize(out_geojson) / 1024 / 1024
print(f"  GeoJSON: {size_geo:.1f} MB")

# Verificar match com dados do censo
censo_path = os.path.join(OUT_DIR, "4_1_acesso_matriculas.json")
with open(censo_path, "r", encoding="utf-8") as f:
    censo = json.load(f)

cod_shape = set(gdf["cod_mun"].astype(str).str[:7].values)
cod_censo = set(censo["por_municipio"]["2025"].keys())

match = cod_shape & cod_censo
only_shape = cod_shape - cod_censo
only_censo = cod_censo - cod_shape

print(f"\nVERIFICACAO DE MATCH:")
print(f"  Municipios no shape: {len(cod_shape)}")
print(f"  Municipios no censo: {len(cod_censo)}")
print(f"  Match:               {len(match)}")
print(f"  So no shape:         {len(only_shape)}")
print(f"  So no censo:         {len(only_censo)}")

if only_censo:
    # Verificar se eh questao de digitos (CO_MUNICIPIO tem 7 digitos no IBGE)
    print(f"\n  Amostra 'so no censo': {list(only_censo)[:5]}")
    print(f"  Amostra 'cod_shape':   {list(cod_shape)[:5]}")

print("\nConcluido!")
