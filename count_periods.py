"""
Script per contare i periodi di indisponibilità invece dei singoli giorni
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def count_indisponibilita_periods():
    """
    Conta i periodi di indisponibilità raggruppando giorni consecutivi
    """
    conn = sqlite3.connect('arbitri.db')
    
    # Ottieni tutte le indisponibilità ordinate
    query = '''
        SELECT cod_mecc, data_indisponibilita, motivo
        FROM indisponibilita 
        ORDER BY cod_mecc, motivo, data_indisponibilita
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return 0
    
    # Converti date
    df['data_indisponibilita'] = pd.to_datetime(df['data_indisponibilita'])
    
    periods = 0
    
    # Raggruppa per arbitro e motivo
    for (cod_mecc, motivo), group in df.groupby(['cod_mecc', 'motivo']):
        dates = sorted(group['data_indisponibilita'].tolist())
        
        if not dates:
            continue
            
        # Conta periodi consecutivi
        current_period_start = dates[0]
        
        for i in range(1, len(dates)):
            # Se la data non è consecutiva alla precedente, inizia un nuovo periodo
            if dates[i] - dates[i-1] > timedelta(days=1):
                periods += 1
                current_period_start = dates[i]
        
        # Aggiungi l'ultimo periodo
        periods += 1
    
    return periods

def get_detailed_periods():
    """
    Ottieni dettagli sui periodi di indisponibilità
    """
    conn = sqlite3.connect('arbitri.db')
    
    query = '''
        SELECT cod_mecc, data_indisponibilita, motivo
        FROM indisponibilita 
        ORDER BY cod_mecc, motivo, data_indisponibilita
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return []
    
    df['data_indisponibilita'] = pd.to_datetime(df['data_indisponibilita'])
    
    periods = []
    
    for (cod_mecc, motivo), group in df.groupby(['cod_mecc', 'motivo']):
        dates = sorted(group['data_indisponibilita'].tolist())
        
        if not dates:
            continue
            
        current_start = dates[0]
        current_end = dates[0]
        
        for i in range(1, len(dates)):
            if dates[i] - dates[i-1] <= timedelta(days=1):
                # Continua il periodo corrente
                current_end = dates[i]
            else:
                # Finisce il periodo corrente e inizia uno nuovo
                periods.append({
                    'cod_mecc': cod_mecc,
                    'motivo': motivo,
                    'inizio': current_start,
                    'fine': current_end,
                    'giorni': (current_end - current_start).days + 1
                })
                current_start = dates[i]
                current_end = dates[i]
        
        # Aggiungi l'ultimo periodo
        periods.append({
            'cod_mecc': cod_mecc,
            'motivo': motivo,
            'inizio': current_start,
            'fine': current_end,
            'giorni': (current_end - current_start).days + 1
        })
    
    return periods

if __name__ == "__main__":
    total_periods = count_indisponibilita_periods()
    print(f"Periodi di indisponibilità totali: {total_periods}")
    
    periods = get_detailed_periods()
    print(f"\nEsempi di periodi (primi 10):")
    for period in periods[:10]:
        print(f"Cod: {period['cod_mecc']}, {period['motivo']}: {period['inizio'].strftime('%d/%m')} - {period['fine'].strftime('%d/%m')} ({period['giorni']} giorni)")