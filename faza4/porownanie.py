"""
Faza 4: Porownanie i analiza
Cel: zestawic ranking grafowy (Faza 2) z rankingiem hydraulicznym (Faza 3)
     i sprawdzic, czy wezly uznane za wazne grafowo sa rowniez wazne hydraulicznie.
"""

import os
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

katalog_skryptu = os.path.dirname(os.path.abspath(__file__))
katalog_output  = os.path.join(katalog_skryptu, 'output')
os.makedirs(katalog_output, exist_ok=True)

sciezka_graf = os.path.join(katalog_skryptu, '..', 'faza 2', 'output', 'ranking_grafowy.csv')
sciezka_hyd  = os.path.join(katalog_skryptu, '..', 'faza3',  'output', 'ranking_hydrauliczny.csv')


# 4.1 – POLACZENIE RANKINGOW
print("=" * 60)
print("4.1 – Polaczenie rankingow grafowego i hydraulicznego")
print("=" * 60)

# wczytujemy oba rankingi
df_graf = pd.read_csv(sciezka_graf, dtype={'node_name': str})
df_hyd  = pd.read_csv(sciezka_hyd,  dtype={'wezel': str})

df_graf = df_graf.rename(columns={'node_name': 'wezel'})

# dodajemy rangi grafowe
df_graf = df_graf.reset_index(drop=True)
df_graf['rank_grafowy'] = df_graf.index + 1

# laczymy obie tabele po nazwie wezla
df_merged = pd.merge(
    df_hyd[['wezel', 'rank_hydrauliczny', 'spadek_cisnienia_m', 'cisnienie_po_awarii_m', 'liczba_rur_zamknietych']],
    df_graf[['wezel', 'rank_grafowy', 'betweenness_score', 'degree_score', 'status']],
    on='wezel',
    how='inner'
)

etykieta_wazny = df_graf['status'].iloc[0]  
# liczba wezlow uznanych za wazne grafowo
n_waznych_graf = (df_graf['status'] == etykieta_wazny).sum()

# sprawdzamy zgodnosc
df_merged['wazny_grafowo']     = df_merged['status'] == etykieta_wazny
df_merged['wazny_hydraulicznie'] = df_merged['rank_hydrauliczny'] <= n_waznych_graf

def etykieta_zgodnosci(row):
    g = row['wazny_grafowo']
    h = row['wazny_hydraulicznie']
    if g and h:
        return 'Zgodnosc (wazny w obu)'
    elif g and not h:
        return 'Tylko grafowo wazny'
    elif not g and h:
        return 'Tylko hydraulicznie wazny'
    else:
        return 'Mniej wazny w obu'

df_merged['zgodnosc'] = df_merged.apply(etykieta_zgodnosci, axis=1)

# Posortuj wg rangi hydraulicznej do wyswietlenia i zapisu
# sorutjemy wedlug rangi hydraulicznej
df_merged = df_merged.sort_values('rank_hydrauliczny').reset_index(drop=True)

# podsumowanie zgodnosci
print(f"\nLiczba wezlow grafowo waznych (prog): {n_waznych_graf}")
print(f"\nRozklad zgodnosci miedzy metodami:")
print(df_merged['zgodnosc'].value_counts().to_string())

print(f"\nTop 15 wg rankingu hydraulicznego:")
kolumny_podglad = ['rank_hydrauliczny', 'wezel', 'status', 'spadek_cisnienia_m', 'rank_grafowy', 'betweenness_score', 'zgodnosc']
print(df_merged[kolumny_podglad].head(15).to_string(index=False))

# pelna tabele porownawcza do CSV
kolumny_csv = [
    'rank_hydrauliczny', 'rank_grafowy', 'wezel',
    'status', 'betweenness_score', 'degree_score',
    'spadek_cisnienia_m', 'cisnienie_po_awarii_m',
    'liczba_rur_zamknietych', 'zgodnosc'
]
sciezka_wyniki = os.path.join(katalog_output, 'porownanie_rankingow.csv')
df_merged[kolumny_csv].to_csv(sciezka_wyniki, index=False)
print(f"\nZapisano: faza4/output/porownanie_rankingow.csv")


# 4.2 – WIZUALIZACJE
print("\n" + "=" * 60)
print("4.2 – Wizualizacje")
print("=" * 60)

KOLORY = {
    'Zgodnosc (wazny w obu)'      : '#2ecc71',   
    'Tylko grafowo wazny'          : '#e74c3c',   
    'Tylko hydraulicznie wazny'    : '#e67e22',   
    'Mniej wazny w obu'            : '#95a5a6',   
}

# wykres 1
fig, ax = plt.subplots(figsize=(10, 7))

for kategoria, kolor in KOLORY.items():
    maska = df_merged['zgodnosc'] == kategoria
    podzb = df_merged[maska]
    ax.scatter(
        podzb['betweenness_score'],
        podzb['spadek_cisnienia_m'],
        c=kolor,
        label=f"{kategoria} (n={maska.sum()})",
        s=70,
        alpha=0.85,
        edgecolors='white',
        linewidths=0.5,
        zorder=3
    )

# wezly, ktore sa w top-10 hydraulicznie lub top-5 grafowo
wezly_do_podpisania = df_merged[
    (df_merged['rank_hydrauliczny'] <= 10) | (df_merged['rank_grafowy'] <= 5)
].copy()

for _, row in wezly_do_podpisania.iterrows():
    ax.annotate(
        f"  {row['wezel']}",
        xy=(row['betweenness_score'], row['spadek_cisnienia_m']),
        fontsize=8,
        color='#2c3e50',
        zorder=4
    )

x = df_merged['betweenness_score'].values
y = df_merged['spadek_cisnienia_m'].values
if np.std(x) > 0:
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    x_linia = np.linspace(x.min(), x.max(), 200)
    ax.plot(x_linia, p(x_linia), '--', color='#7f8c8d', linewidth=1.2,
            label=f'Trend liniowy (r={np.corrcoef(x, y)[0,1]:.2f})', zorder=2)

ax.set_xlabel('Betweenness Centrality (ranking grafowy)', fontsize=12)
ax.set_ylabel('Spadek sredniego cisnienia po awarii [m]', fontsize=12)
ax.set_title('Centralnosc grafowa a krytycznosc hydrauliczna wezlow sieci Net3', fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper right')
ax.grid(True, linestyle='--', alpha=0.4, zorder=1)
ax.axhline(0, color='black', linewidth=0.8, linestyle='-', alpha=0.5)

plt.tight_layout()
sciezka_scatter = os.path.join(katalog_output, 'scatter_centralnosc_vs_cisnienie.png')
plt.savefig(sciezka_scatter, dpi=150, bbox_inches='tight')
plt.close()
print("Zapisano: faza4/output/scatter_centralnosc_vs_cisnienie.png")


# wykres 2
# Bierzemy 20 najwazniejszych hydraulicznie i pokazujemy ich obie rangi
top20 = df_merged.sort_values('rank_hydrauliczny').head(20).copy()

fig, ax = plt.subplots(figsize=(12, 7))

x_pos = np.arange(len(top20))
szerokosc = 0.38

paski_hyd  = ax.bar(x_pos - szerokosc/2, top20['rank_hydrauliczny'],
                    szerokosc, label='Ranga hydrauliczna', color='#2980b9', alpha=0.85)
paski_graf = ax.bar(x_pos + szerokosc/2, top20['rank_grafowy'],
                    szerokosc, label='Ranga grafowa (betweenness)', color='#5d6d7e', alpha=0.85)

ax.set_xticks(x_pos)
ax.set_xticklabels(
    [f"W{row['wezel']}" for _, row in top20.iterrows()],
    rotation=45, ha='right', fontsize=9
)

# Pokoloruj etykiety osi X kolorem kategorii zgodnosci
for etykieta, (_, row) in zip(ax.get_xticklabels(), top20.iterrows()):
    etykieta.set_color(KOLORY.get(row['zgodnosc'], 'black'))

# Etykiety wartosci na paskach
for pasek in paski_hyd:
    h = pasek.get_height()
    ax.text(pasek.get_x() + pasek.get_width()/2, h + 0.3,
            f'{int(h)}', ha='center', va='bottom', fontsize=7, color='#2c3e50')
for pasek in paski_graf:
    h = pasek.get_height()
    ax.text(pasek.get_x() + pasek.get_width()/2, h + 0.3,
            f'{int(h)}', ha='center', va='bottom', fontsize=7, color='#2c3e50')

# Legenda: rangi (gorny lewy), kategorie zgodnosci (gorny prawy)
patche_zgodn = [mpatches.Patch(color=k, label=v) for v, k in KOLORY.items()]
legenda_rangi = ax.legend(fontsize=10, loc='upper left')
legenda_zgodnosci = ax.legend(handles=patche_zgodn, fontsize=8, loc='upper right',
                               title='Kolor etykiety = kategoria zgodnosci')
ax.add_artist(legenda_rangi)

ax.set_xlabel('Wezel sieci', fontsize=12)
ax.set_ylabel('Miejsce w rankingu (nizej = wazniejszy)', fontsize=12)
ax.set_title('Porownanie rang: Top 20 wezlow hydraulicznie krytycznych\n'
             '(niebieski = ranga hyd., szary = ranga grafowa | kolor etykiety = kategoria zgodnosci)', fontsize=11, fontweight='bold')
ax.grid(True, axis='y', linestyle='--', alpha=0.4)

plt.tight_layout()
sciezka_slupkowy = os.path.join(katalog_output, 'ranking_porownanie_slupkowy.png')
plt.savefig(sciezka_slupkowy, dpi=150, bbox_inches='tight')
plt.close()
print("Zapisano: faza4/output/ranking_porownanie_slupkowy.png")

print("\nFaza 4 zakonczona.")
print(f"\nPliki wyjsciowe:")
print(f"  faza4/output/porownanie_rankingow.csv")
print(f"  faza4/output/scatter_centralnosc_vs_cisnienie.png")
print(f"  faza4/output/ranking_porownanie_slupkowy.png")
