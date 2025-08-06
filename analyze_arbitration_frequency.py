import sqlite3
import pandas as pd

def analyze_arbitration_frequency():
    """Analizza la frequenza di arbitraggio per aprile-maggio 2025"""
    conn = sqlite3.connect('arbitri.db')
    
    print("📊 ANALISI FREQUENZA ARBITRAGGIO APRILE-MAGGIO 2025")
    print("="*60)
    
    # Frequenza arbitraggio per arbitro nel periodo esteso
    frequency_query = """
        SELECT 
            a.cognome,
            a.nome,
            a.cod_mecc,
            COUNT(g.numero_gara) as numero_gare,
            GROUP_CONCAT(DISTINCT g.categoria || ' ' || g.girone) as categorie_arbitrate,
            MIN(g.data_gara) as prima_gara,
            MAX(g.data_gara) as ultima_gara
        FROM arbitri a
        LEFT JOIN gare g ON a.cod_mecc = g.cod_mecc
        WHERE g.data_gara BETWEEN '2025-04-01' AND '2025-05-31'
        AND g.ruolo = 'AR'
        GROUP BY a.cod_mecc, a.cognome, a.nome
        ORDER BY numero_gare DESC, a.cognome
    """
    
    frequency_df = pd.read_sql_query(frequency_query, conn)
    
    print(f"🏃 TOP 15 ARBITRI PIÙ ATTIVI (Aprile-Maggio):")
    print("-" * 60)
    for i, row in frequency_df.head(15).iterrows():
        categorie = row['categorie_arbitrate'][:50] + "..." if len(str(row['categorie_arbitrate'])) > 50 else row['categorie_arbitrate']
        print(f"{i+1:2d}. {row['cognome']} {row['nome']:<15} - {row['numero_gare']:2d} gare")
        print(f"    Categorie: {categorie}")
        print(f"    Periodo: {row['prima_gara']} → {row['ultima_gara']}")
        print()
    
    # Statistiche per mese
    april_stats = pd.read_sql_query("""
        SELECT 
            COUNT(DISTINCT g.cod_mecc) as arbitri_attivi,
            COUNT(g.numero_gara) as totale_gare,
            AVG(gare_per_arbitro.numero_gare) as media_gare_per_arbitro
        FROM (
            SELECT cod_mecc, COUNT(*) as numero_gare
            FROM gare 
            WHERE data_gara BETWEEN '2025-04-01' AND '2025-04-30' 
            AND ruolo = 'AR'
            GROUP BY cod_mecc
        ) as gare_per_arbitro
        JOIN gare g ON gare_per_arbitro.cod_mecc = g.cod_mecc
        WHERE g.data_gara BETWEEN '2025-04-01' AND '2025-04-30'
        AND g.ruolo = 'AR'
    """, conn)
    
    may_stats = pd.read_sql_query("""
        SELECT 
            COUNT(DISTINCT g.cod_mecc) as arbitri_attivi,
            COUNT(g.numero_gara) as totale_gare,
            AVG(gare_per_arbitro.numero_gare) as media_gare_per_arbitro
        FROM (
            SELECT cod_mecc, COUNT(*) as numero_gare
            FROM gare 
            WHERE data_gara BETWEEN '2025-05-01' AND '2025-05-31' 
            AND ruolo = 'AR'
            GROUP BY cod_mecc
        ) as gare_per_arbitro
        JOIN gare g ON gare_per_arbitro.cod_mecc = g.cod_mecc
        WHERE g.data_gara BETWEEN '2025-05-01' AND '2025-05-31'
        AND g.ruolo = 'AR'
    """, conn)
    
    print("📅 CONFRONTO MENSILE:")
    print("-" * 30)
    print(f"APRILE 2025:")
    print(f"  👥 Arbitri attivi: {april_stats.iloc[0, 0] if not april_stats.empty else 0}")
    print(f"  🏟️ Totale gare AR: {april_stats.iloc[0, 1] if not april_stats.empty else 0}")
    print(f"  📈 Media gare/arbitro: {april_stats.iloc[0, 2]:.1f}" if not april_stats.empty and april_stats.iloc[0, 2] else "N/A")
    
    print(f"\nMAGGIO 2025:")
    print(f"  👥 Arbitri attivi: {may_stats.iloc[0, 0] if not may_stats.empty else 0}")
    print(f"  🏟️ Totale gare AR: {may_stats.iloc[0, 1] if not may_stats.empty else 0}")
    print(f"  📈 Media gare/arbitro: {may_stats.iloc[0, 2]:.1f}" if not may_stats.empty and may_stats.iloc[0, 2] else "N/A")
    
    # Distribuzione gare
    distribution_query = """
        SELECT 
            numero_gare,
            COUNT(*) as num_arbitri
        FROM (
            SELECT cod_mecc, COUNT(*) as numero_gare
            FROM gare 
            WHERE data_gara BETWEEN '2025-04-01' AND '2025-05-31' 
            AND ruolo = 'AR'
            GROUP BY cod_mecc
        )
        GROUP BY numero_gare
        ORDER BY numero_gare DESC
    """
    
    distribution_df = pd.read_sql_query(distribution_query, conn)
    
    print(f"\n📊 DISTRIBUZIONE FREQUENZA:")
    print("-" * 30)
    for _, row in distribution_df.head(10).iterrows():
        print(f"  {row['numero_gare']:2d} gare: {row['num_arbitri']:3d} arbitri")
    
    conn.close()
    return frequency_df

if __name__ == "__main__":
    analyze_arbitration_frequency()