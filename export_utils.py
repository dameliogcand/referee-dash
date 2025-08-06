"""
Utilità per l'export dei dati in Excel
"""
import pandas as pd
import io
from database import get_arbitri, get_gare_by_week, get_voti_by_week, get_indisponibilita_by_week
from datetime import datetime, timedelta
from utils import get_week_ranges

def export_all_data_to_excel():
    """Esporta tutti i dati in un file Excel con più fogli"""
    
    # Crea un buffer in memoria per il file Excel
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl', mode='w') as writer:
        # Foglio anagrafica arbitri
        arbitri_df = get_arbitri()
        if not arbitri_df.empty:
            arbitri_df.to_excel(writer, sheet_name='Anagrafica Arbitri', index=False)
        
        # Foglio riassuntivo per settimane con categoria + girone
        summary_data = []
        week_ranges = get_week_ranges()
        
        for week_num, (week_start, week_end) in enumerate(week_ranges, 1):
            gare_settimana = get_gare_by_week(week_start, week_end)
            voti_settimana = get_voti_by_week(week_start, week_end)
            indisponibilita_settimana = get_indisponibilita_by_week(week_start, week_end)
            
            if not arbitri_df.empty:
                for _, arbitro in arbitri_df.iterrows():
                    cod_mecc = arbitro['cod_mecc']
                    
                    # Cerca gare per questo arbitro in questa settimana
                    gare_arbitro = gare_settimana[gare_settimana['cod_mecc'] == cod_mecc] if not gare_settimana.empty else pd.DataFrame()
                    
                    # Categoria + Girone (es. "CND A - ECC B")
                    categoria_girone = ""
                    if not gare_arbitro.empty:
                        for _, gara in gare_arbitro.iterrows():
                            categoria = gara.get('categoria', '')
                            girone = gara.get('girone', '')
                            if categoria and girone:
                                if categoria_girone:
                                    categoria_girone += ", "
                                categoria_girone += f"{categoria} {girone}"
                    
                    # Voti per questo arbitro
                    voti_arbitro = ""
                    if not gare_arbitro.empty:
                        for _, gara in gare_arbitro.iterrows():
                            numero_gara = gara['numero_gara']
                            voto_match = voti_settimana[voti_settimana['numero_gara'] == numero_gara] if not voti_settimana.empty else pd.DataFrame()
                            if not voto_match.empty:
                                voto = voto_match.iloc[0]
                                voto_oa = voto.get('voto_oa', '')
                                voto_ot = voto.get('voto_ot', '')
                                if voto_oa or voto_ot:
                                    if voti_arbitro:
                                        voti_arbitro += ", "
                                    voto_str = f"OA:{voto_oa}" if voto_oa else ""
                                    if voto_ot:
                                        voto_str += f" OT:{voto_ot}" if voto_str else f"OT:{voto_ot}"
                                    voti_arbitro += voto_str
                    
                    # Indisponibilità per questo arbitro
                    indisponibilita_arbitro = ""
                    ind_arbitro = indisponibilita_settimana[indisponibilita_settimana['cod_mecc'] == cod_mecc] if not indisponibilita_settimana.empty else pd.DataFrame()
                    if not ind_arbitro.empty:
                        motivi_series = ind_arbitro['motivo'].dropna()
                        motivi = motivi_series.unique() if hasattr(motivi_series, 'unique') else []
                        indisponibilita_arbitro = ', '.join(motivi) if len(motivi) > 0 else "Indisponibile"
                    
                    summary_data.append({
                        'Arbitro': f"{arbitro['cognome']} {arbitro['nome']}",
                        'Cod_Mecc': cod_mecc,
                        'Sezione': arbitro.get('sezione', ''),
                        f'Settimana_{week_num}': categoria_girone,
                        f'Voti_Settimana_{week_num}': voti_arbitro,
                        f'Indisponibilita_Settimana_{week_num}': indisponibilita_arbitro
                    })
        
        # Convert to DataFrame
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            
            # Raggruppa per arbitro e unisci le settimane
            final_summary = {}
            for _, row in summary_df.iterrows():
                arbitro = row['Arbitro']
                if arbitro not in final_summary:
                    final_summary[arbitro] = {
                        'Arbitro': arbitro,
                        'Cod_Mecc': row['Cod_Mecc'],
                        'Sezione': row['Sezione']
                    }
                
                # Aggiungi dati delle settimane
                for col in row.index:
                    col_str = str(col)
                    if col_str.startswith('Settimana_') or col_str.startswith('Voti_') or col_str.startswith('Indisponibilita_'):
                        if col not in final_summary[arbitro]:
                            final_summary[arbitro][col] = row[col]
                        elif row[col]:  # Se c'è un valore non vuoto
                            current_val = final_summary[arbitro][col]
                            if current_val and current_val != row[col]:
                                final_summary[arbitro][col] = f"{current_val}, {row[col]}"
                            elif not current_val:
                                final_summary[arbitro][col] = row[col]
            
            final_df = pd.DataFrame(list(final_summary.values()))
            final_df.to_excel(writer, sheet_name='Riassunto per Settimane', index=False)
        
        # Fogli dettagliati per ogni settimana
        for week_num, (week_start, week_end) in enumerate(week_ranges, 1):
            gare_settimana = get_gare_by_week(week_start, week_end)
            if not gare_settimana.empty:
                # Aggiungi categoria + girone combinata
                gare_settimana['Categoria_Girone'] = gare_settimana.apply(
                    lambda row: f"{row.get('categoria', '')} {row.get('girone', '')}".strip(), axis=1
                )
                gare_settimana.to_excel(writer, sheet_name=f'Settimana_{week_num}', index=False)
    
    buffer.seek(0)
    return buffer

def get_arbitration_stats_by_category():
    """Calcola statistiche di arbitraggio per categoria/girone per ogni arbitro"""
    arbitri_df = get_arbitri()
    
    if arbitri_df.empty:
        return pd.DataFrame()
    
    # Ottieni tutte le gare dal database
    import sqlite3
    conn = sqlite3.connect('arbitri.db')
    
    try:
        # Query per ottenere solo le gare AR (Arbitro) con categoria e girone - esclude QU
        query = '''
            SELECT g.cod_mecc, g.categoria, g.girone, g.numero_gara,
                   a.cognome, a.nome, a.sezione
            FROM gare g
            JOIN arbitri a ON g.cod_mecc = a.cod_mecc
            WHERE g.categoria IS NOT NULL AND g.girone IS NOT NULL 
            AND g.ruolo = 'AR' AND g.ruolo != 'QU'
        '''
        
        gare_df = pd.read_sql_query(query, conn)
        
        if gare_df.empty:
            return pd.DataFrame()
        
        # Crea combinazione categoria + girone
        gare_df['categoria_girone'] = gare_df['categoria'] + ' ' + gare_df['girone']
        
        # Calcola statistiche per arbitro
        stats_list = []
        
        for cod_mecc in arbitri_df['cod_mecc'].unique():
            arbitro_info = arbitri_df[arbitri_df['cod_mecc'] == cod_mecc].iloc[0]
            arbitro_gare = gare_df[gare_df['cod_mecc'] == cod_mecc]
            
            if not arbitro_gare.empty:
                # Conta arbitraggi per categoria/girone
                if hasattr(arbitro_gare['categoria_girone'], 'value_counts'):
                    counts = arbitro_gare['categoria_girone'].value_counts()
                else:
                    counts = pd.Series(arbitro_gare['categoria_girone']).value_counts()
                
                for categoria_girone, count in counts.items():
                    stats_list.append({
                        'Arbitro': f"{arbitro_info['cognome']} {arbitro_info['nome']}",
                        'Cod_Mecc': cod_mecc,
                        'Sezione': arbitro_info.get('sezione', ''),
                        'Categoria_Girone': categoria_girone,
                        'Numero_Arbitraggi': count
                    })
        
        return pd.DataFrame(stats_list)
        
    except Exception as e:
        print(f"Errore nel calcolo statistiche: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def create_complete_excel_export(data_inizio, data_fine, arbitro_selezionato=None):
    """
    Crea un file Excel completo con tutte le informazioni degli arbitri inclusa l'anzianità
    """
    from io import BytesIO
    import pandas as pd
    from database import get_arbitri
    from utils import get_week_dates
    from datetime import datetime
    import sqlite3
    
    # Buffer per il file Excel
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Ottieni i dati degli arbitri
        arbitri_df = get_arbitri()
        
        if arbitri_df.empty:
            # Crea un foglio vuoto se non ci sono dati
            pd.DataFrame(['Nessun dato disponibile']).to_excel(writer, sheet_name='Info', index=False)
            buffer.seek(0)
            return buffer.getvalue()
        
        # Applica filtro arbitro se selezionato
        if arbitro_selezionato and arbitro_selezionato != "Tutti gli arbitri":
            cognome_nome = arbitro_selezionato.split(" ", 1)
            if len(cognome_nome) >= 2:
                cognome_filtro = cognome_nome[0]
                nome_filtro = cognome_nome[1]
                arbitri_df = arbitri_df[
                    (arbitri_df['cognome'] == cognome_filtro) & 
                    (arbitri_df['nome'] == nome_filtro)
                ]
        
        # Connessione database per dati aggiuntivi
        conn = sqlite3.connect('arbitri.db')
        
        # Foglio 1: Anagrafica arbitri con anzianità
        anagrafica_export = arbitri_df.copy()
        
        # Calcola anzianità in anni se presente
        anagrafica_export['anzianita_anni'] = anagrafica_export['anno_anzianita'].apply(
            lambda x: 2025 - x if pd.notna(x) else None
        )
        
        # Seleziona e riordina colonne
        cols_to_export = ['cod_mecc', 'cognome', 'nome', 'sezione', 'eta']
        if 'anno_anzianita' in anagrafica_export.columns:
            cols_to_export.extend(['anzianita_anni', 'anno_anzianita'])
        
        anagrafica_export = anagrafica_export[cols_to_export]
        anagrafica_export.columns = ['Cod_Mecc', 'Cognome', 'Nome', 'Sezione', 'Età'] + (['Anzianità_OT', 'Anno_Inizio_OT'] if 'anno_anzianita' in arbitri_df.columns else [])
        
        anagrafica_export.to_excel(writer, sheet_name='Anagrafica', index=False)
        
        # Foglio 2: Programmazione settimanale con anzianità
        weeks = get_week_dates(data_inizio, data_fine)
        export_data = []
        
        for _, arbitro in arbitri_df.iterrows():
            # Calcola anzianità display
            anzianita_display = ""
            if pd.notna(arbitro.get('anno_anzianita')):
                anni_esperienza = 2025 - int(arbitro['anno_anzianita'])
                anzianita_display = str(anni_esperienza) if anni_esperienza > 0 else "0"
            
            row_data = {
                'Cod_Mecc': arbitro['cod_mecc'],
                'Arbitro': f"{arbitro['cognome']} {arbitro['nome']}",
                'Sezione': arbitro.get('sezione', ''),
                'Anzianità': anzianita_display
            }
            
            # Per ogni settimana, aggiungi le informazioni
            for i, (week_start, week_end) in enumerate(weeks, 1):
                week_start_date = week_start.date() if hasattr(week_start, 'date') else week_start
                week_end_date = week_end.date() if hasattr(week_end, 'date') else week_end
                week_label = f"Settimana_{i}_{week_start_date.strftime('%d_%m')}"
                
                # Query per gare, voti e indisponibilità
                week_content = []
                
                # Gare
                gare_query = '''
                    SELECT categoria, girone, data_gara
                    FROM gare 
                    WHERE cod_mecc = ? AND data_gara BETWEEN ? AND ?
                '''
                gare_df = pd.read_sql_query(gare_query, conn, params=[arbitro['cod_mecc'], week_start_date, week_end_date])
                
                if not gare_df.empty:
                    for _, gara in gare_df.iterrows():
                        if pd.notna(gara['categoria']) and pd.notna(gara['girone']):
                            week_content.append(f"🏃‍♂️ {gara['categoria']} {gara['girone']}")
                
                # Voti
                voti_query = '''
                    SELECT v.voto_oa, v.voto_ot, ot.cognome_ot
                    FROM voti v
                    JOIN gare g ON v.numero_gara = g.numero_gara
                    LEFT JOIN organi_tecnici ot ON v.numero_gara = ot.numero_gara
                    WHERE g.cod_mecc = ? AND g.data_gara BETWEEN ? AND ?
                '''
                voti_df = pd.read_sql_query(voti_query, conn, params=[arbitro['cod_mecc'], week_start_date, week_end_date])
                
                if not voti_df.empty:
                    for _, voto in voti_df.iterrows():
                        voto_str = []
                        if pd.notna(voto['voto_oa']):
                            voto_str.append(f"OA:{voto['voto_oa']}")
                        if pd.notna(voto['voto_ot']):
                            ot_str = f"OT:{voto['voto_ot']}"
                            if pd.notna(voto['cognome_ot']):
                                ot_str += f" ({voto['cognome_ot']})"
                            voto_str.append(ot_str)
                        if voto_str:
                            week_content.append(f"⭐ {' '.join(voto_str)}")
                
                # Indisponibilità
                indisponibilita_query = '''
                    SELECT i.motivo
                    FROM indisponibilita i
                    JOIN arbitri a ON (
                        CAST(i.cod_mecc AS TEXT) = CAST(a.cod_mecc AS TEXT) OR
                        CAST(SUBSTR(a.cod_mecc, -5) AS INTEGER) = CAST(i.cod_mecc AS INTEGER) OR
                        CAST(SUBSTR(a.cod_mecc, -6) AS INTEGER) = CAST(i.cod_mecc AS INTEGER)
                    )
                    WHERE a.cod_mecc = ? AND i.data_indisponibilita BETWEEN ? AND ?
                '''
                indis_df = pd.read_sql_query(indisponibilita_query, conn, params=[arbitro['cod_mecc'], week_start_date, week_end_date])
                
                if not indis_df.empty:
                    motivi = indis_df['motivo'].dropna().unique()
                    if len(motivi) > 0:
                        week_content.append(f"❌ {', '.join(motivi)}")
                
                row_data[week_label] = ' • '.join(week_content) if week_content else ''
            
            export_data.append(row_data)
        
        # Esporta programmazione settimanale
        if export_data:
            programmazione_df = pd.DataFrame(export_data)
            programmazione_df.to_excel(writer, sheet_name='Programmazione_Settimanale', index=False)
        
        # Foglio 3: Tutte le gare del periodo con anzianità
        gare_query = '''
            SELECT g.numero_gara, g.categoria, g.girone, g.data_gara, g.ruolo,
                   a.cognome, a.nome, a.sezione, a.anno_anzianita,
                   CASE WHEN a.anno_anzianita IS NOT NULL THEN (2025 - a.anno_anzianita) ELSE 0 END as anzianita_display
            FROM gare g
            JOIN arbitri a ON g.cod_mecc = a.cod_mecc
            WHERE g.data_gara BETWEEN ? AND ?
            ORDER BY g.data_gara, g.numero_gara
        '''
        gare_complete = pd.read_sql_query(gare_query, conn, params=[data_inizio, data_fine])
        if not gare_complete.empty:
            gare_complete.columns = ['Numero_Gara', 'Categoria', 'Girone', 'Data', 'Ruolo', 'Cognome', 'Nome', 'Sezione', 'Anno_Inizio_OT', 'Anzianità']
            gare_complete.to_excel(writer, sheet_name='Gare_Complete', index=False)
        
        # Foglio 4: Tutti i voti del periodo con anzianità
        voti_query = '''
            SELECT v.numero_gara, v.voto_oa, v.voto_ot, g.data_gara, g.categoria, g.girone,
                   a.cognome, a.nome, a.sezione, ot.cognome_ot, a.anno_anzianita,
                   CASE WHEN a.anno_anzianita IS NOT NULL THEN (2025 - a.anno_anzianita) ELSE 0 END as anzianita_display
            FROM voti v
            JOIN gare g ON v.numero_gara = g.numero_gara
            JOIN arbitri a ON g.cod_mecc = a.cod_mecc
            LEFT JOIN organi_tecnici ot ON v.numero_gara = ot.numero_gara
            WHERE g.data_gara BETWEEN ? AND ?
            ORDER BY g.data_gara, v.numero_gara
        '''
        voti_complete = pd.read_sql_query(voti_query, conn, params=[data_inizio, data_fine])
        if not voti_complete.empty:
            voti_complete.columns = ['Numero_Gara', 'Voto_OA', 'Voto_OT', 'Data', 'Categoria', 'Girone', 'Cognome', 'Nome', 'Sezione', 'OT_Cognome', 'Anno_Inizio_OT', 'Anzianità']
            voti_complete.to_excel(writer, sheet_name='Voti_Complete', index=False)
        
        conn.close()
        
        # Foglio 5: Statistiche del periodo
        arbitri_con_anzianita = len(arbitri_df[arbitri_df['anno_anzianita'].notna()]) if 'anno_anzianita' in arbitri_df.columns else 0
        
        stats_data = {
            'Periodo': [f"{data_inizio.strftime('%d/%m/%Y')} - {data_fine.strftime('%d/%m/%Y')}"],
            'Arbitri_Totali': [len(arbitri_df)],
            'Arbitri_Con_Anzianità_OT': [arbitri_con_anzianita],
            'Settimane_Analizzate': [len(weeks)],
            'Export_Data': [datetime.now().strftime('%d/%m/%Y %H:%M:%S')],
            'Filtro_Applicato': [arbitro_selezionato if arbitro_selezionato != "Tutti gli arbitri" else "Nessuno"]
        }
        pd.DataFrame(stats_data).to_excel(writer, sheet_name='Statistiche_Export', index=False)
    
    buffer.seek(0)
    return buffer.getvalue()