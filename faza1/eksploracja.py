import wntr
import wntr.graphics
import matplotlib.pyplot as plt
import os

# 1.1 - Wczytanie sieci Net3
inp_file = wntr.library.model_library.get_filepath('Net3')
wn = wntr.network.WaterNetworkModel(inp_file)
print("Siec Net3 wczytana poprawnie.")
print(f"Plik: {inp_file}")

# 1.3 - Eksploracja sieci
print("\n--- Parametry sieci ---")
print(f"Wezly (junctions):  {wn.num_junctions}")
print(f"Rury (pipes):       {wn.num_pipes}")
print(f"Zbiorniki (tanks):  {wn.num_tanks}")
print(f"Rezerwuary:         {wn.num_reservoirs}")
print(f"Pompy (pumps):      {wn.num_pumps}")

# 1.3 - Wizualizacja
os.makedirs("faza1/output", exist_ok=True)

import matplotlib
matplotlib.use('Agg')  # zapis do pliku bez okna

fig, ax = plt.subplots(figsize=(10, 8))
wntr.graphics.plot_network(wn, ax=ax, title="Topologia sieci Net3")
plt.savefig("faza1/output/siec_net3.png", dpi=150, bbox_inches='tight')
print("\nWizualizacja zapisana: faza1/output/siec_net3.png")