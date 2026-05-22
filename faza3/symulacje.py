import os
import warnings
import wntr
import wntr.network
import pandas as pd

# Sciezki do folderow i plikow
katalog_skryptu = os.path.dirname(os.path.abspath(__file__))
katalog_output  = os.path.join(katalog_skryptu, 'output')
os.makedirs(katalog_output, exist_ok=True)

# Plik CSV z Fazy 2
sciezka_ranking_graf = os.path.join(katalog_skryptu, '..', 'faza 2', 'output', 'ranking_grafowy.csv')

inp_file = wntr.library.model_library.get_filepath('Net3')


# 3.1 – SYMULACJA BAZOWA (sieć w normalnej pracy, bez awarii)
print("=" * 60)
print("3.1 – Symulacja bazowa sieci Net3 (bez awarii)")
print("=" * 60)

wn_baza = wntr.network.WaterNetworkModel(inp_file)
sym_baza = wntr.sim.WNTRSimulator(wn_baza)

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    wyniki_baza = sym_baza.run_sim()

cisnienie_baza = wyniki_baza.node['pressure']

# wazne sa tylko wezly typu junction
junctions = wn_baza.junction_name_list

# srednie cisnienie dla kazdego wezla usrednione po calej dobie
srednie_na_wezel_baza = cisnienie_baza[junctions].mean(axis=0)

# srednie cisnienie calej sieci
srednie_siec_baza = float(srednie_na_wezel_baza.mean())

print(f"Liczba węzłów (junctions): {len(junctions)}")
print(f"Średnie ciśnienie sieci [punkt odniesienia]: {srednie_siec_baza:.4f} m")

# zapis cisnien bazowych 
df_baza = srednie_na_wezel_baza.reset_index()
df_baza.columns = ['wezel', 'srednie_cisnienie_bazowe_m']
df_baza.to_csv(os.path.join(katalog_output, 'cisnienie_bazowe.csv'), index=False)
print("Zapisano: faza3/output/cisnienie_bazowe.csv")


# 3.2 – SCENARIUSZE AWARII - pracujemy na kazdym wezle
print("\n" + "=" * 60)
print("3.2 – Scenariusze awarii")
print("=" * 60)

# wczytujemy ranking grafowy z fazy drugiej
df_ranking_graf = pd.read_csv(sciezka_ranking_graf, dtype={'node_name': str})

df_ranking_graf = df_ranking_graf.reset_index(drop=True)
df_ranking_graf['rank_grafowy'] = df_ranking_graf.index + 1

n_waznych    = (df_ranking_graf['status'] == 'Ważny (Krytyczny)').sum()
n_mniej_wazn = (df_ranking_graf['status'] == 'Mniej ważny').sum()
print(f"Wczytano {len(df_ranking_graf)} węzłów z rankingu grafowego:")
print(f"  - Ważny (Krytyczny): {n_waznych}")
print(f"  - Mniej ważny:       {n_mniej_wazn}")
print()

wyniki_awarii = []

for _, row in df_ranking_graf.iterrows():
    wezel_id    = str(row['node_name'])
    kategoria   = str(row['status'])
    rank_graf   = int(row['rank_grafowy'])

    if wezel_id not in junctions:
        print(f"  [POMINIĘTO] {wezel_id} – brak w liście junctions")
        continue

    wn_awaria = wntr.network.WaterNetworkModel(inp_file)

    # zamykamy rury podlaczone do testowanego wezla
    rury_wezla = []
    for pipe_name, pipe in wn_awaria.pipes():
        if pipe.start_node_name == wezel_id or pipe.end_node_name == wezel_id:
            rury_wezla.append(pipe_name)
            pipe.initial_status = wntr.network.LinkStatus.Closed

    if not rury_wezla:
        print(f"  [POMINIĘTO] {wezel_id} – brak rur połączonych")
        continue

    # uruchamiamy symulacje z izolowanym wezlem
    try:
        sym_awaria = wntr.sim.WNTRSimulator(wn_awaria)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            wyniki_aw = sym_awaria.run_sim()

        # srednie cisnienie sieci po awarii
        cisnienie_po   = wyniki_aw.node['pressure'][junctions].mean(axis=0)
        srednie_siec_po = float(cisnienie_po.mean())

        # spadek cisnienia wzgledem stanu bazowego
        spadek = srednie_siec_baza - srednie_siec_po

        wyniki_awarii.append({
            'wezel'                 : wezel_id,
            'rank_grafowy'          : rank_graf,
            'kategoria_grafowa'     : kategoria,
            'betweenness_score'     : row['betweenness_score'],
            'cisnienie_bazowe_m'    : round(srednie_siec_baza, 4),
            'cisnienie_po_awarii_m' : round(srednie_siec_po,   4),
            'spadek_cisnienia_m'    : round(spadek,             4),
            'liczba_rur_zamknietych': len(rury_wezla),
        })

        print(
            f"  [{kategoria[:5]}] "
            f"Węzeł {wezel_id:>5} (rank graf: {rank_graf:>3}) | "
            f"rury: {len(rury_wezla)} | "
            f"spadek: {spadek:+.3f} m"
        )

    except Exception as e:
        print(f"  [BŁĄD]    Węzeł {wezel_id}: {e}")

# zapis wynikow awarii do csv
df_wyniki = pd.DataFrame(wyniki_awarii)
sciezka_wyniki = os.path.join(katalog_output, 'wyniki_awarii.csv')
df_wyniki.to_csv(sciezka_wyniki, index=False)
print(f"\nZapisano: faza3/output/wyniki_awarii.csv  ({len(df_wyniki)} rekordów)")


# 3.3 – RANKING HYDRAULICZNY
print("\n" + "=" * 60)
print("3.3 – Ranking hydrauliczny")
print("=" * 60)

df_ranking_hyd = (
    df_wyniki
    .sort_values(by='spadek_cisnienia_m', ascending=False)
    .reset_index(drop=True)
)

df_ranking_hyd['rank_hydrauliczny'] = df_ranking_hyd.index + 1

kolumny_csv = [
    'rank_hydrauliczny', 'wezel', 'kategoria_grafowa',
    'betweenness_score', 'spadek_cisnienia_m',
    'cisnienie_po_awarii_m', 'rank_grafowy',
    'liczba_rur_zamknietych',
]
df_ranking_hyd[kolumny_csv].to_csv(
    os.path.join(katalog_output, 'ranking_hydrauliczny.csv'), index=False
)

print("Top 10 węzłów najbardziej krytycznych hydraulicznie:")
print(
    df_ranking_hyd[
        ['rank_hydrauliczny', 'wezel', 'kategoria_grafowa', 'spadek_cisnienia_m', 'rank_grafowy']
    ]
    .head(10)
    .to_string(index=False)
)
print("\nZapisano: faza3/output/ranking_hydrauliczny.csv")
print("\nFaza 3 zakonczona.")
