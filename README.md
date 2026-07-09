# Analiza Krytyczności Węzłów Sieci Wodociągowej Net3💧

Celem projektu jest identyfikacja i porównanie kluczowych węzłów w sieci wodociągowej Net3 przy użyciu algorytmów analizy grafów oraz symulacji awarii. Projekt realizowany w zespole dwuosobowym. 

Badania opierają się na modelu sieci wodociągowej **Net3** (92 węzły, 117 przewodów) i zostały podzielone na dwa podejścia:
1. **Analiza Grafowa:** Modelowanie sieci jako grafu nieskierowanego w bazie Neo4j i wyznaczenie rankingu węzłów na podstawie algorytmu centralności pośrednictwa Betweenness Centrality, który identyfikuje punkty kluczowe dla działania sieci.
2. **Analiza Hydrauliczna:** Przeprowadzenie 92 symulacji awarii poprzez sekwencyjne odcinanie każdego węzła wraz z przyległymi przewodamiT w celu zbadania skutków: spadków ciśnień dobowych, generowania ciśnień ujemnych oraz identyfikacji stref niedoboru wody <br><br>

## Wykorzystane Technologie i Biblioteki 📚
* **Python 3.14+** – główny język skryptowy projektu.
* **Neo4j & Neo4j Graph Data Science (GDS)** – grafowa baza danych oraz implementacja algorytmów centralności pośrednictwa *Betweenness Centrality* i stopnia *Degree Centrality*.
* **WNTR (Water Network Tool for Resilience)** – pakiet oparty na silniku EPANET do symulacji hydraulicznych, model DDA.
* **Pandas & NumPy** – przetwarzanie danych, transformacja rankingów i analiza statystyczna.
* **SciPy** – obliczenia współczynników korelacji rangowych.
* **Matplotlib** – generowanie wykresów porównawczych i analiz trendów. <br><br>


## Setup i Uruchomienie 🛠️

### Konfiguracja Zmiennych Środowiskowych 
Projekt wykorzystuje plik `.env` do przechowywania danych logowania do bazy Neo4j.

* Skopiuj plik `.env.example` znajdujący się w głównym katalogu i zmień jego nazwę na `.env`.
* Otwórz plik `.env` i uzupełnij dane:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=TwojeHaslo
```

### Instalacja Zależności
Uruchom terminal w głównym folderze projektu i zainstaluj wymagane pakiety Pythona:
```
python -m pip install -r requirements.txt
```

### Uruchomienie Bazy Danych
Przed uruchomieniem skryptów upewnij się, że Twoja lokalna baza danych w programie Neo4j Desktop z zainstalowaną wtyczką Graph Data Science jest włączona i posiada status **Active/Running**. <br><br>

## Output projektu 📤
Uruchomienie skryptów z poszczególnych faz generuje następujące pliki:

- **faza1/output/siec_net3.png** - Wygenerowana wizualizacja topologii sieci wodociągowej Net3. 

- **faza2/output/ranking_grafowy.csv** – Lista węzłów z obliczonymi metrykami centralności oraz kwalifikacją ważności opartą na algorytmie uskoku.

- **faza3/output/cisnienie_bazowe.csv** - Parametry ciśnienia hydraulicznego w warunkach bezawaryjnej pracy układu.

- **faza3/output/wyniki_awarii.csv** - Parametry uzyskane z symulacji awarii, spadek średniego ciśnienia, minimalne ciśnienie chwilowe w dobie, flaga wystąpienia ciśnienia ujemnego, liczba węzłów poniżej progu eksploatacyjnego.

- **faza4/output/porownanie_rankingow.csv** – Zestawione pozycje węzłów z obu metod.

- **faza4/output/scatter_centralnosc_vs_cisnienie.png** – Wykres ilustrujący korelację i trend między metryką grafową a rzeczywistym spadkiem ciśnienia.

- **faza4/output/ranking_porownanie_slupkowy.png** – Wykres słupkowy prezentujący Top 20 najbardziej krytycznych węzłów hydraulicznych i zestawiający je z ich pozycją w rankingu grafowym.