"""
Processore per file di anzianità arbitri
"""
import pandas as pd
import pdfplumber
import re
from database import update_arbitro_anzianita, get_arbitri

def process_anzianita_file(uploaded_file):
    """Processa file con anzianità arbitri"""
    try:
        file_name = uploaded_file.name.lower()
        
        if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
            return process_anzianita_excel(uploaded_file)
        elif file_name.endswith('.pdf'):
            return process_anzianita_pdf(uploaded_file)
        else:
            return {'success': False, 'message': 'Formato file non supportato per anzianità'}
            
    except Exception as e:
        return {'success': False, 'message': f'Errore nell\'elaborazione anzianità: {str(e)}'}

def process_anzianita_excel(uploaded_file):
    """Processa file Excel con anzianità"""
    try:
        # Leggi il file Excel
        df = pd.read_excel(uploaded_file)
        
        # Cerca le colonne rilevanti (flessibile per diverse strutture)
        column_mapping = {}
        
        for col in df.columns:
            col_lower = str(col).lower()
            if any(word in col_lower for word in ['cognome', 'surname']):
                column_mapping['cognome'] = col
            elif any(word in col_lower for word in ['nome', 'name']):
                column_mapping['nome'] = col
            elif any(word in col_lower for word in ['anzianita', 'anzianità', 'anno', 'year', 'esperienza']):
                column_mapping['anzianita'] = col
        
        if 'cognome' not in column_mapping or 'anzianita' not in column_mapping:
            return {'success': False, 'message': 'Colonne cognome e anzianità non trovate nel file'}
        
        # Processa i dati
        arbitri_db = get_arbitri()
        updated_count = 0
        
        for _, row in df.iterrows():
            cognome = str(row[column_mapping['cognome']]).strip().upper()
            anzianita = row[column_mapping['anzianita']]
            
            # Cerca l'arbitro nel database
            arbitro_match = arbitri_db[arbitri_db['cognome'].str.upper() == cognome]
            
            if not arbitro_match.empty:
                cod_mecc = arbitro_match.iloc[0]['cod_mecc']
                
                # Converti anzianità in numero
                if pd.notna(anzianita):
                    try:
                        anno_anzianita = int(float(anzianita))
                        if update_arbitro_anzianita(cod_mecc, anno_anzianita):
                            updated_count += 1
                    except (ValueError, TypeError):
                        continue
        
        return {
            'success': True, 
            'message': f'Anzianità aggiornata per {updated_count} arbitri'
        }
        
    except Exception as e:
        return {'success': False, 'message': f'Errore nell\'elaborazione Excel anzianità: {str(e)}'}

def process_anzianita_pdf(uploaded_file):
    """Processa file PDF con anzianità dalla graduatoria"""
    try:
        # Leggi il PDF
        with pdfplumber.open(uploaded_file) as pdf:
            full_text = ''
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + '\n'
        
        lines = full_text.split('\n')
        arbitri_db = get_arbitri()
        updated_count = 0
        
        print(f"Processando {len(lines)} righe del PDF graduatoria...")
        
        # Pattern per la graduatoria: Pos COGNOME_NOME SEZIONE ... Età Anz
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Salta header e righe non dati
            if any(word in line.upper() for word in ['POS.', 'COGNOME E NOME', 'FEDERAZIONE', 'GRADUATORIA', 'PAGINA', 'DOCUMENTO CREATO']):
                continue
            
            # Pattern migliorato per graduatoria: Pos NOME_COGNOME SEZIONE ... Età Anz
            # Esempio: "1 ABOU EL ELLA OMAR MIL 2 S 29 5"
            pattern = r'^\s*(\d+)\s+([A-Z\'\s]+?)\s+([A-Z0-9]+)\s+.*?\s+(\d+)\s+(\d+)\s*$'
            match = re.search(pattern, line)
            
            if match:
                pos = match.group(1)
                nome_cognome_completo = match.group(2).strip()
                sezione = match.group(3).strip()
                eta = match.group(4)
                anzianita_ot = match.group(5)
                
                # Separa cognome e nome
                # La maggior parte degli arbitri ha COGNOME NOME, ma alcuni hanno cognomi composti
                parts = nome_cognome_completo.split()
                if len(parts) >= 2:
                    # Prova prima con ultimo come nome, resto come cognome
                    cognome = ' '.join(parts[:-1])
                    nome = parts[-1]
                    
                    # Se non trova match, prova con primo come cognome, resto come nome
                    if not find_arbitro_match(arbitri_db, cognome, nome):
                        cognome = parts[0]
                        nome = ' '.join(parts[1:]) if len(parts) > 1 else ""
                    
                    try:
                        anzianita_anni = int(anzianita_ot)
                        
                        # Cerca l'arbitro nel database
                        arbitro_match = find_arbitro_match(arbitri_db, cognome, nome)
                        
                        if arbitro_match is not None:
                            cod_mecc = arbitro_match['cod_mecc']
                            if update_arbitro_anzianita(cod_mecc, anzianita_anni):
                                updated_count += 1
                                print(f"✓ {cognome} {nome} -> {anzianita_anni} anni OT")
                                
                    except (ValueError, TypeError) as e:
                        print(f"Errore conversione per {nome_cognome_completo}: {e}")
                        continue
        
        return {
            'success': True, 
            'message': f'Anzianità OT aggiornata per {updated_count} arbitri dalla graduatoria'
        }
        
    except Exception as e:
        return {'success': False, 'message': f'Errore nell\'elaborazione PDF graduatoria: {str(e)}'}

def find_arbitro_match(arbitri_db, cognome, nome):
    """Cerca un arbitro nel database con match flessibile"""
    if arbitri_db.empty or not cognome:
        return None
    
    # Prima prova con cognome esatto
    match = arbitri_db[arbitri_db['cognome'].str.upper() == cognome.upper()]
    
    # Se non trovato, prova con cognome parziale (prima parola)
    if match.empty and ' ' in cognome:
        first_part = cognome.split()[0]
        match = arbitri_db[arbitri_db['cognome'].str.upper().str.contains(first_part, regex=False, na=False)]
    
    # Se non trovato, prova con cognome che contiene la prima parte
    if match.empty:
        match = arbitri_db[arbitri_db['cognome'].str.upper().str.contains(cognome.split()[0], regex=False, na=False)]
    
    # Raffina con il nome se ci sono più match e il nome è disponibile
    if len(match) > 1 and nome:
        nome_match = match[match['nome'].str.upper().str.contains(nome.split()[0], regex=False, na=False)]
        if not nome_match.empty:
            match = nome_match
    
    return match.iloc[0] if not match.empty else None