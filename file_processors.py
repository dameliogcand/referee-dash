import pandas as pd
import re

# Import pdfplumber with fallback
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("Warning: pdfplumber not available. PDF processing will be disabled.")
from database import upsert_arbitro, upsert_gara, upsert_voto, upsert_indisponibilita, upsert_organo_tecnico
from datetime import datetime, timedelta
import io
from typing import Dict, Any, Union

def process_arbitri_file(file) -> Dict[str, Any]:
    """Processa il file Excel degli arbitri"""
    try:
        # Leggi il file Excel con engine esplicito
        df = pd.read_excel(file, engine='openpyxl')
        
        # Normalizza i nomi delle colonne (rimuovi spazi e converti in minuscolo)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('.', '_')
        
        # Mappatura possibili nomi colonne
        column_mapping = {
            'cod_mecc': ['cod_mecc', 'cod_mecc_', 'codice_meccanografico', 'cod__mecc', 'codmecc', 'cod meccanografico', 'cod', 'codice'],
            'cognome': ['cognome', 'surname', 'last_name'],
            'nome': ['nome', 'name', 'first_name'],
            'sezione': ['sezione', 'section', 'sez'],
            'eta': ['eta', 'età', 'age', 'anni', 'years']
        }
        
        # Trova le colonne effettive
        actual_columns = {}
        for standard_name, possible_names in column_mapping.items():
            for possible_name in possible_names:
                if possible_name in df.columns:
                    actual_columns[standard_name] = possible_name
                    break
        
        # Verifica che le colonne essenziali siano presenti
        required_columns = ['cod_mecc', 'cognome', 'nome']
        missing_columns = [col for col in required_columns if col not in actual_columns]
        
        if missing_columns:
            return {
                'success': False,
                'message': f"Colonne mancanti nel file: {', '.join(missing_columns)}. Colonne trovate: {', '.join(df.columns.tolist())}"
            }
        
        # Processa ogni riga
        processed_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                cod_mecc_raw = str(row[actual_columns['cod_mecc']]).strip()
                cognome = str(row[actual_columns['cognome']]).strip()
                nome = str(row[actual_columns['nome']]).strip()
                
                # Verifica che i campi essenziali non siano vuoti
                if not cod_mecc_raw or cod_mecc_raw == 'nan' or not cognome or cognome == 'nan' or not nome or nome == 'nan':
                    continue
                
                # Usa il codice meccanografico completo per l'anagrafica
                cod_mecc = cod_mecc_raw
                
                # Campi opzionali
                sezione = None
                if 'sezione' in actual_columns:
                    sezione_val = str(row[actual_columns['sezione']]).strip()
                    if sezione_val and sezione_val != 'nan':
                        sezione = sezione_val
                
                eta = None
                if 'eta' in actual_columns:
                    try:
                        eta_val = row[actual_columns['eta']]
                        if pd.notna(eta_val):
                            eta = int(float(eta_val))
                    except (ValueError, TypeError):
                        pass
                
                # Inserisci nel database
                if upsert_arbitro(cod_mecc, cognome, nome, sezione, eta):
                    processed_count += 1
                else:
                    errors.append(f"Errore nell'inserimento arbitro {cognome} {nome}")
                    
            except Exception as e:
                errors.append(f"Errore alla riga {str(idx + 1)}: {str(e)}")
        
        if errors:
            error_msg = f"Elaborati {processed_count} arbitri con {len(errors)} errori"
            if len(errors) <= 5:
                error_msg += f": {'; '.join(errors)}"
            return {'success': True, 'message': error_msg}
        else:
            return {'success': True, 'message': f"Elaborati con successo {processed_count} arbitri"}
            
    except Exception as e:
        return {'success': False, 'message': f"Errore nella lettura del file: {str(e)}"}

def process_gare_file(file) -> Dict[str, Any]:
    """Processa il file Excel delle gare (CRA01)"""
    try:
        # Leggi il file Excel con engine esplicito
        df = pd.read_excel(file, engine='openpyxl')
        
        # Gestisce colonne generiche del CRA01 con mappatura specifica
        if any(col.startswith('Column') for col in df.columns):
            # Mappatura specifica per file CRA01
            cra01_mapping = {
                'Column2': 'numero_gara',    # Numero_Gara - Colonna B
                'Column18': 'cod_mecc',      # Cod_Mecc - Colonna R
                'Column19': 'cognome',       # Cognome - Colonna S
                'Column7': 'data_gara',      # Data_Gara - Colonna G
                'Column3': 'categoria',      # Categoria - Colonna C
                'Column4': 'girone',         # Girone - Colonna D
                'Column17': 'ruolo'          # Ruolo - Colonna Q
            }
            
            # Rinomina le colonne usando la mappatura CRA01
            df = df.rename(columns=cra01_mapping)
        
        # Normalizza i nomi delle colonne
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('.', '_')
        
        # Mappatura possibili nomi colonne
        column_mapping = {
            'numero_gara': ['numero_gara', 'num_gara', 'gara', 'n_gara', 'numero', 'n°_gara', 'num gara', 'n gara'],
            'cod_mecc': ['cod_mecc', 'cod_mecc_', 'codice_meccanografico', 'cod__mecc', 'codmecc', 'arbitro', 'cod meccanografico', 'cod', 'codice'],
            'data_gara': ['data_gara', 'data', 'date', 'giorno', 'data gara'],
            'categoria': ['categoria', 'campionato', 'championship', 'serie', 'cat'],
            'girone': ['girone', 'group', 'gruppo'],
            'ruolo': ['ruolo', 'role', 'function', 'funzione'],
            'cognome': ['cognome', 'surname', 'last_name'],
            'squadra_casa': ['squadra_casa', 'casa', 'home', 'team_casa', 'squadra casa'],
            'squadra_trasferta': ['squadra_trasferta', 'ospite', 'away', 'team_ospite', 'trasferta', 'squadra trasferta', 'squadra ospite']
        }
        
        # Trova le colonne effettive
        actual_columns = {}
        for standard_name, possible_names in column_mapping.items():
            for possible_name in possible_names:
                if possible_name in df.columns:
                    actual_columns[standard_name] = possible_name
                    break
        
        # Verifica colonne essenziali
        required_columns = ['numero_gara', 'cod_mecc']
        missing_columns = [col for col in required_columns if col not in actual_columns]
        
        if missing_columns:
            return {
                'success': False,
                'message': f"Colonne mancanti nel file: {', '.join(missing_columns)}. Colonne trovate: {', '.join(df.columns.tolist())}"
            }
        
        # Processa ogni riga
        processed_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                numero_gara = str(row[actual_columns['numero_gara']]).strip()
                cod_mecc_raw = str(row[actual_columns['cod_mecc']]).strip()
                
                # Verifica campi essenziali
                if not numero_gara or numero_gara == 'nan' or not cod_mecc_raw or cod_mecc_raw == 'nan':
                    continue
                
                # Per le gare CRA01, usa il codice meccanografico completo (no troncamento)
                # Il matching con l'anagrafica verrà fatto nel database
                cod_mecc = cod_mecc_raw
                
                # Campi opzionali
                data_gara = None
                if 'data_gara' in actual_columns:
                    try:
                        data_val = row[actual_columns['data_gara']]
                        if pd.notna(data_val):
                            if isinstance(data_val, str):
                                # Prova diversi formati data
                                for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                                    try:
                                        data_gara = datetime.strptime(data_val.strip(), fmt).date()
                                        break
                                    except ValueError:
                                        continue
                            else:
                                data_gara = pd.to_datetime(data_val).date()
                    except:
                        pass
                
                categoria = None
                if 'categoria' in actual_columns:
                    cat_val = str(row[actual_columns['categoria']]).strip()
                    if cat_val and cat_val != 'nan':
                        categoria = cat_val
                
                girone = None
                if 'girone' in actual_columns:
                    girone_val = str(row[actual_columns['girone']]).strip()
                    if girone_val and girone_val != 'nan':
                        girone = girone_val
                
                ruolo = None
                if 'ruolo' in actual_columns:
                    ruolo_val = str(row[actual_columns['ruolo']]).strip()
                    if ruolo_val and ruolo_val != 'nan':
                        ruolo = ruolo_val
                
                cognome_arbitro = None
                if 'cognome' in actual_columns:
                    cognome_val = str(row[actual_columns['cognome']]).strip()
                    if cognome_val and cognome_val != 'nan':
                        cognome_arbitro = cognome_val
                
                squadra_casa = None
                if 'squadra_casa' in actual_columns:
                    casa_val = str(row[actual_columns['squadra_casa']]).strip()
                    if casa_val and casa_val != 'nan':
                        squadra_casa = casa_val
                
                squadra_trasferta = None
                if 'squadra_trasferta' in actual_columns:
                    trasferta_val = str(row[actual_columns['squadra_trasferta']]).strip()
                    if trasferta_val and trasferta_val != 'nan':
                        squadra_trasferta = trasferta_val
                
                # Inserisci nel database
                if upsert_gara(numero_gara, cod_mecc, data_gara, categoria, squadra_casa, squadra_trasferta, girone, ruolo, cognome_arbitro):
                    processed_count += 1
                    
                    # Se il ruolo non è 0 e abbiamo un cognome, potrebbe essere un OT - salva nella tabella organi_tecnici
                    if ruolo and ruolo != '0' and cognome_arbitro and cognome_arbitro != 'nan':
                        try:
                            # Verifica se il codice del ruolo è numerico (indica che è un OT)
                            if ruolo.isdigit() and int(ruolo) != 0:
                                upsert_organo_tecnico(numero_gara, ruolo, cognome_arbitro)
                        except (ValueError, TypeError):
                            pass  # Ignora errori nel parsing del ruolo
                else:
                    errors.append(f"Errore nell'inserimento gara {numero_gara}")
                    
            except Exception as e:
                errors.append(f"Errore alla riga {str(idx + 1)}: {str(e)}")
        
        if errors:
            error_msg = f"Elaborate {processed_count} gare con {len(errors)} errori"
            if len(errors) <= 5:
                error_msg += f": {'; '.join(errors)}"
            return {'success': True, 'message': error_msg}
        else:
            return {'success': True, 'message': f"Elaborate con successo {processed_count} gare"}
            
    except Exception as e:
        return {'success': False, 'message': f"Errore nella lettura del file: {str(e)}"}

def process_voti_pdf(file) -> Dict[str, Any]:
    """Processa il file PDF dei voti"""
    if not PDFPLUMBER_AVAILABLE:
        return {'success': False, 'message': "PDF processing non disponibile. Installa pdfplumber per elaborare i file PDF."}
    
    try:
        processed_count = 0
        errors = []
        
        # Leggi il PDF
        pdf_content = file.read()
        pdf_file = io.BytesIO(pdf_content)
        
        with pdfplumber.open(pdf_file) as pdf:
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
        
        if not full_text.strip():
            return {'success': False, 'message': "Impossibile estrarre testo dal PDF"}
        
        # Processa riga per riga per estrarre i voti
        lines = full_text.split('\n')
        found_matches = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Pattern per righe con numero gara e voti
            # Cerca righe che iniziano con numero di 3-4 cifre seguito da dati e voti alla fine
            match = re.match(r'(\d{3,4})\s+.*?([0-9,]+)(?:\s+([0-9,]+))?\s*$', line)
            
            if match:
                found_matches = True
                try:
                    numero_gara = match.group(1)
                    voto_oa_str = match.group(2).replace(',', '.')
                    voto_ot_str = match.group(3).replace(',', '.') if match.group(3) else None
                    
                    # Converti i voti in float
                    voto_oa = None
                    voto_ot = None
                    
                    try:
                        voto_oa_val = float(voto_oa_str)
                        if 0 <= voto_oa_val <= 10:  # Validazione range voto
                            voto_oa = voto_oa_val
                    except (ValueError, TypeError):
                        continue  # Salta questa riga se il voto OA non è valido
                    
                    if voto_ot_str:
                        try:
                            voto_ot_val = float(voto_ot_str)
                            if 0 <= voto_ot_val <= 10:  # Validazione range voto
                                voto_ot = voto_ot_val
                        except (ValueError, TypeError):
                            pass  # OT può essere None se non valido
                    
                    # Inserisci solo se almeno OA è valido
                    if voto_oa is not None:
                        if upsert_voto(numero_gara, voto_oa, voto_ot):
                            processed_count += 1
                        else:
                            errors.append(f"Errore nell'inserimento voto per gara {numero_gara}")
                    
                except Exception as e:
                    errors.append(f"Errore nel processare riga: {str(e)}")
        
        if not found_matches:
            # Fallback: cerca solo numeri che potrebbero essere voti
            lines = full_text.split('\n')
            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Cerca pattern più semplici
                numbers = re.findall(r'\b\d+(?:[.,]\d+)?\b', line)
                if len(numbers) >= 3:  # Almeno numero gara + 2 voti
                    try:
                        numero_gara = numbers[0]
                        voto_oa = float(numbers[1].replace(',', '.'))
                        voto_ot = float(numbers[2].replace(',', '.'))
                        
                        if 0 <= voto_oa <= 10 and 0 <= voto_ot <= 10:
                            if upsert_voto(numero_gara, voto_oa, voto_ot):
                                processed_count += 1
                            found_matches = True
                    except:
                        continue
        
        if processed_count == 0:
            return {
                'success': False, 
                'message': f"Nessun voto estratto dal PDF. Testo estratto (primi 500 caratteri): {full_text[:500]}"
            }
        
        if errors:
            error_msg = f"Elaborati {processed_count} voti con {len(errors)} errori"
            if len(errors) <= 3:
                error_msg += f": {'; '.join(errors)}"
            return {'success': True, 'message': error_msg}
        else:
            return {'success': True, 'message': f"Elaborati con successo {processed_count} voti"}
            
    except Exception as e:
        return {'success': False, 'message': f"Errore nella lettura del PDF: {str(e)}"}

def process_indisponibilita_file(file) -> Dict[str, Any]:
    """Processa il file Excel delle indisponibilità"""
    try:
        # Leggi il file Excel con engine esplicito
        df = pd.read_excel(file, engine='openpyxl')
        
        # Normalizza i nomi delle colonne
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('.', '_')
        
        # Gestisce colonne generiche per file indisponibilità
        if any(col.startswith('Column') for col in df.columns):
            # Mappatura specifica per file indisponibilità
            indisponibilita_mapping = {
                'Column1': 'cod_mecc',        # Cod_Mecc - Colonna A
                'Column2': 'data_inizio',     # Data - Colonna B  
                'Column3': 'qualifica',       # Qualifica - Colonna C
                'Column4': 'motivo'           # Motivo - Colonna D
            }
            # Rinomina le colonne usando la mappatura
            df = df.rename(columns=indisponibilita_mapping)
        
        # Mappatura possibili nomi colonne
        column_mapping = {
            'cod_mecc': ['cod_mecc', 'cod_mecc_', 'codice_meccanografico', 'cod__mecc', 'codmecc', 'arbitro', 'cod meccanografico', 'cod', 'codice'],
            'data_inizio': ['inizio', 'data_inizio', 'start_date', 'data_indisponibilita', 'data', 'date'],
            'data_fine': ['fine', 'data_fine', 'end_date', 'data_fine_indisponibilita'],
            'motivo': ['motivo', 'reason', 'causa', 'note', 'motivazione', 'osservazioni'],
            'qualifica': ['qualifica', 'qualification', 'qual', 'tipo', 'ruolo']
        }
        
        # Trova le colonne effettive
        actual_columns = {}
        for standard_name, possible_names in column_mapping.items():
            for possible_name in possible_names:
                if possible_name in df.columns:
                    actual_columns[standard_name] = possible_name
                    break
        
        # Verifica colonne essenziali
        required_columns = ['cod_mecc', 'data_inizio']
        missing_columns = [col for col in required_columns if col not in actual_columns]
        
        if missing_columns:
            return {
                'success': False,
                'message': f"Colonne mancanti nel file: {', '.join(missing_columns)}. Colonne trovate: {', '.join(df.columns.tolist())}"
            }
        
        # Processa ogni riga
        processed_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                cod_mecc_raw = str(row[actual_columns['cod_mecc']]).strip()
                
                # Verifica campo essenziale
                if not cod_mecc_raw or cod_mecc_raw == 'nan':
                    continue
                
                # Usa il codice meccanografico completo per le indisponibilità
                cod_mecc = cod_mecc_raw
                
                # Data inizio indisponibilità
                data_inizio = None
                try:
                    data_val = row[actual_columns['data_inizio']]
                    if pd.notna(data_val):
                        if isinstance(data_val, str):
                            # Prova diversi formati data
                            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                                try:
                                    data_inizio = datetime.strptime(data_val.strip(), fmt).date()
                                    break
                                except ValueError:
                                    continue
                        else:
                            data_inizio = pd.to_datetime(data_val).date()
                except Exception:
                    errors.append(f"Errore nel parsing della data inizio alla riga {str(idx + 1)}")
                    continue
                
                if data_inizio is None:
                    continue
                
                # Data fine indisponibilità (opzionale)
                data_fine = None
                if 'data_fine' in actual_columns:
                    try:
                        data_val = row[actual_columns['data_fine']]
                        if pd.notna(data_val):
                            if isinstance(data_val, str):
                                # Prova diversi formati data
                                for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                                    try:
                                        data_fine = datetime.strptime(data_val.strip(), fmt).date()
                                        break
                                    except ValueError:
                                        continue
                            else:
                                data_fine = pd.to_datetime(data_val).date()
                    except:
                        pass
                
                # Motivo (opzionale)
                motivo = None
                if 'motivo' in actual_columns:
                    motivo_val = str(row[actual_columns['motivo']]).strip()
                    if motivo_val and motivo_val != 'nan':
                        motivo = motivo_val
                
                # Qualifica (opzionale)
                qualifica = None
                if 'qualifica' in actual_columns:
                    qualifica_val = str(row[actual_columns['qualifica']]).strip()
                    if qualifica_val and qualifica_val != 'nan':
                        qualifica = qualifica_val
                
                # Se c'è una data fine, crea record per ogni giorno del periodo
                # Altrimenti usa solo la data inizio
                dates_to_insert = []
                if data_fine and data_fine >= data_inizio:
                    # Crea un record per ogni giorno del periodo
                    current_date = data_inizio
                    while current_date <= data_fine:
                        dates_to_insert.append(current_date)
                        # Aggiungi un giorno
                        current_date = current_date + timedelta(days=1)
                else:
                    dates_to_insert.append(data_inizio)
                
                # Inserisci nel database per ogni data
                for date_to_insert in dates_to_insert:
                    if upsert_indisponibilita(cod_mecc, date_to_insert, motivo, qualifica):
                        processed_count += 1
                    else:
                        errors.append(f"Errore nell'inserimento indisponibilità per {cod_mecc} il {date_to_insert}")
                    
            except Exception as e:
                errors.append(f"Errore alla riga {str(idx + 1)}: {str(e)}")
        
        if errors:
            error_msg = f"Elaborate {processed_count} indisponibilità con {len(errors)} errori"
            if len(errors) <= 5:
                error_msg += f": {'; '.join(errors)}"
            return {'success': True, 'message': error_msg}
        else:
            return {'success': True, 'message': f"Elaborate con successo {processed_count} indisponibilità"}
            
    except Exception as e:
        return {'success': False, 'message': f"Errore nella lettura del file: {str(e)}"}