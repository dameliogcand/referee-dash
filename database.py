import sqlite3
import pandas as pd
from datetime import datetime

def init_database():
    """Inizializza il database SQLite con le tabelle necessarie"""
    conn = sqlite3.connect('arbitri.db')
    cursor = conn.cursor()
    
    # Tabella arbitri (anagrafica)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS arbitri (
            cod_mecc TEXT PRIMARY KEY,
            cognome TEXT NOT NULL,
            nome TEXT NOT NULL,
            sezione TEXT,
            eta INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabella gare
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gare (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_gara TEXT NOT NULL,
            cod_mecc TEXT NOT NULL,
            data_gara DATE,
            campionato TEXT,
            girone TEXT,
            ruolo TEXT,
            cognome_arbitro TEXT,
            squadra_casa TEXT,
            squadra_trasferta TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cod_mecc) REFERENCES arbitri (cod_mecc),
            UNIQUE(numero_gara, cod_mecc)
        )
    ''')
    
    # Aggiungi colonne se non esistono già (per compatibilità con database esistenti)
    cursor.execute("PRAGMA table_info(gare)")
    existing_columns = [column[1] for column in cursor.fetchall()]
    
    if 'categoria' not in existing_columns:
        cursor.execute('ALTER TABLE gare ADD COLUMN categoria TEXT')
    if 'girone' not in existing_columns:
        cursor.execute('ALTER TABLE gare ADD COLUMN girone TEXT')
    if 'ruolo' not in existing_columns:
        cursor.execute('ALTER TABLE gare ADD COLUMN ruolo TEXT')
    if 'cognome_arbitro' not in existing_columns:
        cursor.execute('ALTER TABLE gare ADD COLUMN cognome_arbitro TEXT')
        
    # Aggiungi colonna anzianità alla tabella arbitri se non esiste
    cursor.execute("PRAGMA table_info(arbitri)")
    arbitri_columns = [column[1] for column in cursor.fetchall()]
    
    if 'anno_anzianita' not in arbitri_columns:
        cursor.execute('ALTER TABLE arbitri ADD COLUMN anno_anzianita INTEGER')
    
    # Tabella voti
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_gara TEXT NOT NULL,
            voto_oa REAL,
            voto_ot REAL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(numero_gara)
        )
    ''')
    
    # Tabella indisponibilità
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS indisponibilita (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cod_mecc TEXT NOT NULL,
            data_indisponibilita DATE NOT NULL,
            motivo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cod_mecc) REFERENCES arbitri (cod_mecc),
            UNIQUE(cod_mecc, data_indisponibilita)
        )
    ''')
    
    # Tabella organi_tecnici per gestire gli OT con i loro cognomi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS organi_tecnici (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_gara TEXT NOT NULL,
            cod_ot TEXT NOT NULL,
            cognome_ot TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(numero_gara, cod_ot)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_arbitri():
    """Recupera tutti gli arbitri dal database"""
    conn = sqlite3.connect('arbitri.db')
    try:
        df = pd.read_sql_query("SELECT * FROM arbitri ORDER BY cognome, nome", conn)
        return df
    except Exception as e:
        print(f"Errore nel recupero arbitri: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_gare_by_week(week_start, week_end):
    """Recupera le gare assegnate per una settimana specifica"""
    conn = sqlite3.connect('arbitri.db')
    try:
        query = '''
            SELECT g.*, a.cognome, a.nome 
            FROM gare g
            JOIN arbitri a ON g.cod_mecc = a.cod_mecc
            WHERE g.data_gara BETWEEN ? AND ?
            ORDER BY g.data_gara, g.numero_gara
        '''
        df = pd.read_sql_query(query, conn, params=[week_start.date(), week_end.date()])
        if not df.empty and 'data_gara' in df.columns:
            df['data_gara'] = pd.to_datetime(df['data_gara'])
        return df
    except Exception as e:
        print(f"Errore nel recupero gare: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_voti_by_week(week_start, week_end):
    """Recupera i voti per una settimana specifica"""
    conn = sqlite3.connect('arbitri.db')
    try:
        query = '''
            SELECT v.*, g.data_gara
            FROM voti v
            JOIN gare g ON v.numero_gara = g.numero_gara
            WHERE g.data_gara BETWEEN ? AND ?
            ORDER BY g.data_gara, v.numero_gara
        '''
        df = pd.read_sql_query(query, conn, params=[week_start.date(), week_end.date()])
        if not df.empty and 'data_gara' in df.columns:
            df['data_gara'] = pd.to_datetime(df['data_gara'])
        return df
    except Exception as e:
        print(f"Errore nel recupero voti: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_indisponibilita_by_week(week_start, week_end):
    """Recupera le indisponibilità per una settimana specifica"""
    conn = sqlite3.connect('arbitri.db')
    try:
        query = '''
            SELECT i.*, a.cognome, a.nome
            FROM indisponibilita i
            JOIN arbitri a ON i.cod_mecc = a.cod_mecc
            WHERE i.data_indisponibilita BETWEEN ? AND ?
            ORDER BY i.data_indisponibilita, a.cognome
        '''
        df = pd.read_sql_query(query, conn, params=[week_start.date(), week_end.date()])
        if not df.empty and 'data_indisponibilita' in df.columns:
            df['data_indisponibilita'] = pd.to_datetime(df['data_indisponibilita'])
        return df
    except Exception as e:
        print(f"Errore nel recupero indisponibilità: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def upsert_arbitro(cod_mecc, cognome, nome, sezione=None, eta=None, anno_anzianita=None):
    """Inserisce o aggiorna un arbitro"""
    conn = sqlite3.connect('arbitri.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO arbitri (cod_mecc, cognome, nome, sezione, eta, anno_anzianita, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (cod_mecc, cognome, nome, sezione, eta, anno_anzianita))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore nell'inserimento arbitro: {e}")
        return False
    finally:
        conn.close()

def update_arbitro_anzianita(cod_mecc, anno_anzianita):
    """Aggiorna solo l'anno di anzianità di un arbitro"""
    conn = sqlite3.connect('arbitri.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE arbitri 
            SET anno_anzianita = ?, updated_at = CURRENT_TIMESTAMP
            WHERE cod_mecc = ?
        ''', (anno_anzianita, cod_mecc))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Errore nell'aggiornamento anzianità: {e}")
        return False
    finally:
        conn.close()

def find_matching_arbitro_cod_mecc(cod_mecc_cra01):
    """Trova il codice meccanografico corrispondente nell'anagrafica arbitri.
    Il CRA01 contiene codici a 7 cifre, l'anagrafica ha codici a 8 cifre."""
    conn = sqlite3.connect('arbitri.db')
    cursor = conn.cursor()
    
    try:
        # Il CRA01 ha codici a 7 cifre, l'anagrafica a 8 cifre
        # Cerca un arbitro il cui cod_mecc termina con il codice del CRA01
        cursor.execute('''
            SELECT cod_mecc FROM arbitri 
            WHERE SUBSTR(cod_mecc, -7) = ? OR cod_mecc = ?
            LIMIT 1
        ''', (str(cod_mecc_cra01), str(cod_mecc_cra01)))
        
        result = cursor.fetchone()
        return result[0] if result else cod_mecc_cra01  # Se non trova match, usa il codice originale
    except Exception as e:
        print(f"Errore nella ricerca codice arbitro: {e}")
        return cod_mecc_cra01  # Fallback al codice originale
    finally:
        conn.close()

def upsert_gara(numero_gara, cod_mecc, data_gara=None, categoria=None, squadra_casa=None, squadra_trasferta=None, girone=None, ruolo=None, cognome_arbitro=None):
    """Inserisce o aggiorna una gara"""
    conn = sqlite3.connect('arbitri.db')
    cursor = conn.cursor()
    
    try:
        # Trova il codice meccanografico corrispondente nell'anagrafica
        matched_cod_mecc = find_matching_arbitro_cod_mecc(cod_mecc)
        
        cursor.execute('''
            INSERT OR REPLACE INTO gare 
            (numero_gara, cod_mecc, data_gara, categoria, girone, ruolo, cognome_arbitro, squadra_casa, squadra_trasferta, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (numero_gara, matched_cod_mecc, data_gara, categoria, girone, ruolo, cognome_arbitro, squadra_casa, squadra_trasferta))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore nell'inserimento gara: {e}")
        return False
    finally:
        conn.close()

def upsert_voto(numero_gara, voto_oa=None, voto_ot=None, note=None):
    """Inserisce o aggiorna un voto"""
    conn = sqlite3.connect('arbitri.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO voti (numero_gara, voto_oa, voto_ot, note, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (numero_gara, voto_oa, voto_ot, note))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore nell'inserimento voto: {e}")
        return False
    finally:
        conn.close()

def upsert_indisponibilita(cod_mecc, data_indisponibilita, motivo=None, qualifica=None):
    """Inserisce o aggiorna un'indisponibilità"""
    conn = sqlite3.connect('arbitri.db')
    cursor = conn.cursor()
    
    try:
        # Verifica se la colonna qualifica esiste
        cursor.execute("PRAGMA table_info(indisponibilita)")
        columns = [col[1] for col in cursor.fetchall()]
        has_qualifica = 'qualifica' in columns
        
        if has_qualifica:
            cursor.execute('''
                INSERT OR REPLACE INTO indisponibilita (cod_mecc, data_indisponibilita, motivo, qualifica, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (cod_mecc, data_indisponibilita, motivo, qualifica))
        else:
            cursor.execute('''
                INSERT OR REPLACE INTO indisponibilita (cod_mecc, data_indisponibilita, motivo, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (cod_mecc, data_indisponibilita, motivo))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore nell'inserimento indisponibilità: {e}")
        return False
    finally:
        conn.close()

def upsert_organo_tecnico(numero_gara, cod_ot, cognome_ot):
    """Inserisce o aggiorna un organo tecnico per una gara"""
    conn = sqlite3.connect('arbitri.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO organi_tecnici (numero_gara, cod_ot, cognome_ot, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (numero_gara, cod_ot, cognome_ot))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore nell'inserimento organo tecnico: {e}")
        return False
    finally:
        conn.close()
