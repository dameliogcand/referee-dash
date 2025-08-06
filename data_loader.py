"""
Modulo per il caricamento automatico dei dati dell'anagrafica arbitri
"""
import pandas as pd
from file_processors import process_arbitri_file
import os

def load_arbitri_anagrafica():
    """Carica automaticamente l'anagrafica arbitri dal file incluso nel progetto"""
    anagrafica_file = 'arbitri_anagrafica.xlsx'
    
    if os.path.exists(anagrafica_file):
        try:
            with open(anagrafica_file, 'rb') as f:
                result = process_arbitri_file(f)
                return result
        except Exception as e:
            return {'success': False, 'message': f'Errore nel caricamento anagrafica: {str(e)}'}
    else:
        return {'success': False, 'message': 'File anagrafica arbitri non trovato'}

def ensure_anagrafica_loaded():
    """Assicura che l'anagrafica sia caricata nel database"""
    from database import get_arbitri
    
    # Controlla se ci sono già arbitri nel database
    arbitri_df = get_arbitri()
    
    # Controlla se l'anagrafrica è già stata caricata correttamente
    # (deve avere almeno 200 arbitri per essere considerata completa)
    if len(arbitri_df) >= 200:
        return {'success': True, 'message': f'Anagrafica già caricata: {len(arbitri_df)} arbitri'}
    else:
        # Pulisci eventuali dati parziali e ricarica
        import sqlite3
        conn = sqlite3.connect('arbitri.db')
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM arbitri')
            conn.commit()
        except:
            pass
        finally:
            conn.close()
        
        # Carica l'anagrafica
        result = load_arbitri_anagrafica()
        return result