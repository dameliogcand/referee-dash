"""
Script per popolare completamente il database con tutti i dati necessari
"""
import pandas as pd
import pdfplumber
import re
from database import init_database, upsert_arbitro, upsert_gara, upsert_voto, upsert_indisponibilita, update_arbitro_anzianita
from file_processors import process_gare_file, process_voti_pdf, process_indisponibilita_file

def populate_complete_database():
    """Popola il database con tutti i dati necessari"""
    print("Inizializzazione database...")
    init_database()
    
    # 1. Carica anagrafica arbitri
    print("Caricamento anagrafica arbitri...")
    load_arbitri_anagrafica()
    
    # 2. Carica anzianità da graduatoria
    print("Caricamento anzianità da graduatoria...")
    load_anzianita_from_graduatoria()
    
    # 3. Carica gare (CRA01)
    print("Caricamento gare...")
    load_gare_data()
    
    # 4. Carica voti
    print("Caricamento voti...")
    load_voti_data()
    
    # 5. Carica indisponibilità
    print("Caricamento indisponibilità...")
    load_indisponibilita_data()
    
    print("Database popolato completamente!")
    
    return {
        'success': True,
        'message': 'Database popolato completamente',
        'stats': 'Tutti i dati caricati'
    }

def populate_complete_database_if_empty():
    """Popola il database solo se è vuoto (per Streamlit Cloud)"""
    import sqlite3
    
    conn = sqlite3.connect('arbitri.db')
    cursor = conn.cursor()
    
    try:
        # Controlla se il database ha dati
        cursor.execute("SELECT COUNT(*) FROM arbitri")
        arbitri_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM gare") 
        gare_count = cursor.fetchone()[0]
        
        # Se il database è vuoto, popolalo
        if arbitri_count == 0 or gare_count == 0:
            print(f"Database vuoto rilevato ({arbitri_count} arbitri, {gare_count} gare), popolamento automatico...")
            return populate_complete_database()
        else:
            return {
                'success': True,
                'message': f'Database già popolato: {arbitri_count} arbitri, {gare_count} gare'
            }
    except Exception as e:
        print(f"Errore controllo database: {e}")
        return {'success': False, 'message': f'Errore: {e}'}
    finally:
        conn.close()

def load_arbitri_anagrafica():
    """Carica anagrafica arbitri dal file Excel"""
    try:
        df = pd.read_excel('arbitri_anagrafica.xlsx')
        
        # Mappa colonne (flessibile per diversi formati)
        column_mapping = {}
        for col in df.columns:
            col_lower = str(col).lower()
            if any(word in col_lower for word in ['cod', 'mecc', 'codice']):
                column_mapping['cod_mecc'] = col
            elif 'cognome' in col_lower:
                column_mapping['cognome'] = col
            elif 'nome' in col_lower:
                column_mapping['nome'] = col
            elif any(word in col_lower for word in ['sez', 'sezione']):
                column_mapping['sezione'] = col
            elif any(word in col_lower for word in ['eta', 'età', 'age']):
                column_mapping['eta'] = col
        
        count = 0
        for _, row in df.iterrows():
            try:
                cod_mecc = str(row[column_mapping['cod_mecc']]).strip()
                cognome = str(row[column_mapping['cognome']]).strip().upper()
                nome = str(row[column_mapping['nome']]).strip().upper()
                sezione = str(row[column_mapping.get('sezione', '')]).strip() if pd.notna(row.get(column_mapping.get('sezione', ''), '')) else None
                eta = int(row[column_mapping.get('eta', 0)]) if pd.notna(row.get(column_mapping.get('eta', ''), 0)) and row.get(column_mapping.get('eta', ''), 0) != '' else None
                
                if cod_mecc and cognome and nome:
                    if upsert_arbitro(cod_mecc, cognome, nome, sezione, eta):
                        count += 1
            except Exception as e:
                print(f"Errore riga arbitro: {e}")
                continue
        
        print(f"Caricati {count} arbitri dall'anagrafica")
        
    except Exception as e:
        print(f"Errore caricamento anagrafica: {e}")

def load_anzianita_from_graduatoria():
    """Carica anzianità dal PDF graduatoria"""
    try:
        with pdfplumber.open('attached_assets/Stampa_Graduatoria_1754169546859.pdf') as pdf:
            full_text = ''
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + '\n'
        
        lines = full_text.split('\n')
        updated_count = 0
        
        for line in lines:
            line = line.strip()
            if not line or any(word in line.upper() for word in ['POS.', 'COGNOME E NOME', 'FEDERAZIONE', 'GRADUATORIA', 'PAGINA', 'DOCUMENTO']):
                continue
            
            # Pattern per graduatoria: pos nome_cognome sezione ... età anzianità
            pattern = r'^\s*(\d+)\s+([A-Z\'\s]+?)\s+([A-Z0-9]+)\s+.*?\s+(\d+)\s+(\d+)\s*$'
            match = re.search(pattern, line)
            
            if match:
                nome_cognome = match.group(2).strip()
                anzianita = match.group(5)
                
                # Divide nome e cognome
                parts = nome_cognome.split()
                if len(parts) >= 2:
                    if len(parts) == 2:
                        cognome, nome = parts[0], parts[1]
                    elif len(parts) == 3:
                        cognome, nome = parts[0], ' '.join(parts[1:])
                    else:
                        cognome, nome = ' '.join(parts[:-1]), parts[-1]
                    
                    try:
                        anni_ot = int(anzianita)
                        anno_inizio = 2025 - anni_ot
                        
                        # Trova arbitro nel database e aggiorna anzianità
                        from database import get_arbitri
                        arbitri_db = get_arbitri()
                        
                        # Match esatto prima
                        match_exact = arbitri_db[arbitri_db['cognome'].str.upper() == cognome.upper()]
                        
                        # Se non trovato, match parziale
                        if match_exact.empty:
                            match_partial = arbitri_db[
                                arbitri_db['cognome'].str.upper().str.contains(cognome.split()[0], regex=False, na=False)
                            ]
                            if not match_partial.empty:
                                match_exact = match_partial
                        
                        if not match_exact.empty:
                            cod_mecc = match_exact.iloc[0]['cod_mecc']
                            if update_arbitro_anzianita(cod_mecc, anno_inizio):
                                updated_count += 1
                                
                    except (ValueError, TypeError):
                        continue
        
        print(f"Aggiornata anzianità per {updated_count} arbitri")
        
    except Exception as e:
        print(f"Errore caricamento anzianità: {e}")

def load_gare_data():
    """Carica dati gare dal file CRA01"""
    try:
        class MockFile:
            def __init__(self, path):
                self.name = path.split('/')[-1]
                self.path = path
            
            def read(self):
                with open(self.path, 'rb') as f:
                    return f.read()
        
        gare_file = MockFile('attached_assets/cra01_1754149850022.xlsx')
        result = process_gare_file(gare_file)
        print(f"Gare: {result['message']}")
        
    except Exception as e:
        print(f"Errore caricamento gare: {e}")

def load_voti_data():
    """Carica dati voti dal PDF"""
    try:
        class MockFile:
            def __init__(self, path):
                self.name = path.split('/')[-1]
                self.path = path
            
            def read(self):
                with open(self.path, 'rb') as f:
                    return f.read()
        
        voti_file = MockFile('attached_assets/Stampa_Elenco_Voti_1754149850023.pdf')
        result = process_voti_pdf(voti_file)
        print(f"Voti: {result['message']}")
        
    except Exception as e:
        print(f"Errore caricamento voti: {e}")

def load_indisponibilita_data():
    """Carica dati indisponibilità"""
    try:
        class MockFile:
            def __init__(self, path):
                self.name = path.split('/')[-1]
                self.path = path
            
            def read(self):
                with open(self.path, 'rb') as f:
                    return f.read()
        
        indis_file = MockFile('attached_assets/Indisponibili_1754149850022.xlsx')
        result = process_indisponibilita_file(indis_file)
        print(f"Indisponibilità: {result['message']}")
        
    except Exception as e:
        print(f"Errore caricamento indisponibilità: {e}")

if __name__ == "__main__":
    populate_complete_database()