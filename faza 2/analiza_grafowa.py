import wntr
import pandas as pd
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

katalog_skryptu = os.path.dirname(os.path.abspath(__file__))
sciezka_env = os.path.join(katalog_skryptu, ".env")

load_dotenv(sciezka_env)

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "Projekt5!")

def wyczysc_baze(tx):
    tx.run("MATCH (n) DETACH DELETE n")

def importuj_siec(tx, wn):
    print("Importowanie węzłów...")
    for node_name, node in wn.junctions():
        x, y = node.coordinates
        tx.run(
            "MERGE (j:Junction {name: $name}) SET j.x = $x, j.y = $y",
            name=node_name, x=x, y=y
        )
    print("Importowanie rur...")
    for pipe_name, pipe in wn.pipes():
        start_node = pipe.start_node_name
        end_node = pipe.end_node_name
        length = pipe.length 
        
        tx.run(
            """
            MATCH (a:Junction {name: $start})
            MATCH (b:Junction {name: $end})
            MERGE (a)-[r:PIPE {name: $name}]->(b)
            SET r.length = $length
            """,
            start=start_node, end=end_node, name=pipe_name, length=length
        )

def oblicz_ranking_gds(driver):
    with driver.session() as session:
        print("\nUruchamianie analizy grafowej GDS...")
        session.run("CALL gds.graph.drop('siec_projekt', false)")
        print("Tworzenie projekcji grafu w GDS...")
        session.run("""
            CALL gds.graph.project(
              'siec_projekt',
              'Junction',
              {
                PIPE: {
                  type: 'PIPE',
                  orientation: 'UNDIRECTED'
                }
              }
            )
        """)
        
        print("Obliczanie Betweenness Centrality...")
        res_betweenness = session.run("""
            CALL gds.betweenness.stream('siec_projekt')
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).name AS node_name, score AS betweenness_score
        """)
        df_betweenness = pd.DataFrame([dict(r) for r in res_betweenness])
        
        print("Obliczanie Degree Centrality...")
        res_degree = session.run("""
            CALL gds.degree.stream('siec_projekt')
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).name AS node_name, score AS degree_score
        """)
        df_degree = pd.DataFrame([dict(r) for r in res_degree])
        
        # Połączenie obu miar w tabelę
        df_final = pd.merge(df_betweenness, df_degree, on="node_name")
        
        # Sortowanie węzłów malejąco według centralności pośrednictwa
        df_final = df_final.sort_values(by="betweenness_score", ascending=False).reset_index(drop=True)
        
        scores = df_final['betweenness_score'].values
        max_drop = 0
        split_index = 0
 
        for i in range(len(scores) - 1):
            drop = scores[i] - scores[i+1]
            if drop > max_drop:
                max_drop = drop
                split_index = i
        
        df_final['status'] = 'Mniej ważny'
        df_final.loc[:split_index, 'status'] = 'Ważny (Krytyczny)'
        
        # 6. Eksport wyników do pliku CSV
        katalog_skryptu = os.path.dirname(os.path.abspath(__file__))
        katalog_output = os.path.join(katalog_skryptu, "output")
        
        os.makedirs(katalog_output, exist_ok=True)
        sciezka_csv = os.path.join(katalog_output, "ranking_grafowy.csv")
        df_final.to_csv(sciezka_csv, index=False)
        
        print(f"\nRanking grafowy został zapisany do: {sciezka_csv}")
        print(f"Algorytm wyodrębnił {split_index + 1} węzłów jako krytyczne.")
        print("\nTop 5 najbardziej krytycznych węzłów wg grafu:")
        print(df_final.head(5))

inp_file = wntr.library.model_library.get_filepath('Net3')
wn = wntr.network.WaterNetworkModel(inp_file)

with GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
    with driver.session() as session:
        print("Czyszczenie bazy danych...")
        session.execute_write(wyczysc_baze)
        
        print("Wgrywanie nowego grafu sieci...")
        session.execute_write(importuj_siec, wn)
        print("Sieć Net3 została zaimportowana do Neo4j.")
    oblicz_ranking_gds(driver)