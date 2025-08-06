from datetime import datetime, timedelta
import locale

def get_week_dates(start_date, end_date):
    """
    Genera una lista di tuple (inizio_settimana, fine_settimana) 
    per il periodo specificato
    """
    weeks = []
    current_date = start_date
    
    while current_date <= end_date:
        # Trova l'inizio della settimana (lunedì)
        week_start = current_date - timedelta(days=current_date.weekday())
        
        # Trova la fine della settimana (domenica)
        week_end = week_start + timedelta(days=6)
        
        # Assicurati che non superi la data di fine
        if week_end > end_date:
            week_end = end_date
        
        # Aggiungi solo se c'è sovrapposizione con il periodo richiesto
        if week_start <= end_date and week_end >= start_date:
            # Limita alle date del periodo richiesto
            actual_start = max(week_start, start_date)
            actual_end = min(week_end, end_date)
            weeks.append((actual_start, actual_end))
        
        # Vai alla settimana successiva
        current_date = week_end + timedelta(days=1)
        
        # Evita loop infiniti
        if len(weeks) > 15:  # Massimo 15 settimane (per includere aprile + maggio)
            break
    
    return weeks

def format_week_display(week_start, week_end):
    """
    Formatta la visualizzazione di una settimana
    """
    try:
        if week_start == week_end:
            return week_start.strftime("%d/%m/%Y")
        else:
            return f"{week_start.strftime('%d/%m/%Y')} - {week_end.strftime('%d/%m/%Y')}"
    except:
        return f"{week_start} - {week_end}"

def format_date_italian(date):
    """
    Formatta una data in formato italiano
    """
    if date is None:
        return ""
    
    try:
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Nomi dei giorni in italiano
        giorni = [
            'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 
            'Venerdì', 'Sabato', 'Domenica'
        ]
        
        # Nomi dei mesi in italiano
        mesi = [
            'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
            'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'
        ]
        
        giorno_settimana = giorni[date.weekday()]
        mese = mesi[date.month - 1]
        
        return f"{giorno_settimana} {date.day} {mese} {date.year}"
    except:
        return str(date)

def validate_cod_mecc(cod_mecc):
    """
    Valida il formato del codice meccanografico
    """
    if not cod_mecc or not isinstance(cod_mecc, str):
        return False
    
    # Rimuovi spazi e converti in maiuscolo
    cod_mecc = cod_mecc.strip().upper()
    
    # Controlli di base (adatta secondo il formato effettivo)
    if len(cod_mecc) < 3 or len(cod_mecc) > 20:
        return False
    
    # Deve contenere almeno un carattere alfanumerico
    if not any(c.isalnum() for c in cod_mecc):
        return False
    
    return True

def validate_voto(voto):
    """
    Valida un voto (deve essere tra 0 e 10)
    """
    try:
        voto_float = float(voto)
        return 0 <= voto_float <= 10
    except (ValueError, TypeError):
        return False

def clean_filename(filename):
    """
    Pulisce il nome del file per evitare caratteri problematici
    """
    import re
    
    # Rimuovi caratteri non validi
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limita la lunghezza
    if len(filename) > 100:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:100-len(ext)-1] + '.' + ext if ext else name[:100]
    
    return filename

def format_arbitro_with_anzianita(cognome, nome, anno_anzianita=None):
    """
    Formatta il nome dell'arbitro con l'anzianità se disponibile
    Es: ROSSI MARIO (5a)
    """
    nome_completo = f"{cognome} {nome}"
    
    if anno_anzianita and anno_anzianita > 0:
        anni_esperienza = 2025 - anno_anzianita
        if anni_esperienza > 0:
            nome_completo += f" ({anni_esperienza}a)"
    
    return nome_completo

def get_current_season():
    """
    Determina la stagione calcistica corrente
    """
    now = datetime.now()
    
    # La stagione calcistica inizia generalmente ad agosto
    if now.month >= 8:
        return f"{now.year}/{now.year + 1}"
    else:
        return f"{now.year - 1}/{now.year}"

def parse_team_names(team_string):
    """
    Estrae i nomi delle squadre da una stringa del tipo "Team A vs Team B"
    """
    if not team_string:
        return None, None
    
    # Pattern comuni per separare le squadre
    separators = [' vs ', ' - ', ' v ', ' VS ', ' V ', '-']
    
    for sep in separators:
        if sep in team_string:
            parts = team_string.split(sep, 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
    
    return team_string.strip(), None

def get_week_ranges():
    """Restituisce tutte le settimane di aprile e maggio 2025 dal lunedì alla domenica"""
    # Periodo esteso: 1 aprile - 31 maggio 2025
    period_start = datetime(2025, 4, 1)
    period_end = datetime(2025, 5, 31, 23, 59, 59)
    
    # Trova il primo lunedì del periodo (o il lunedì precedente se il periodo inizia dopo lunedì)
    first_day = period_start
    if first_day.weekday() != 0:  # Se non è lunedì
        first_monday = first_day - timedelta(days=first_day.weekday())
    else:
        first_monday = first_day
    
    weeks = []
    current_monday = first_monday
    
    while current_monday <= period_end:
        week_end = current_monday + timedelta(days=6, hours=23, minutes=59, seconds=59)  # Domenica fine giornata
        
        # Controlla se la settimana si sovrappone al periodo aprile-maggio
        if current_monday <= period_end and week_end >= period_start:
            weeks.append((current_monday, week_end))
        
        current_monday += timedelta(days=7)
        
        if len(weeks) > 10:  # Sicurezza per evitare loop infiniti (max 10 settimane per 2 mesi)
            break
    
    return weeks

def format_date_range(start_date, end_date):
    """Formatta un range di date per la visualizzazione"""
    return f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m/%Y')}"
