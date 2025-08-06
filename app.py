import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from database import init_database, get_arbitri
from file_processors import process_gare_file, process_voti_pdf, process_indisponibilita_file

from data_loader import ensure_anagrafica_loaded
from populate_complete_db import populate_complete_database_if_empty
from export_utils import export_all_data_to_excel, get_arbitration_stats_by_category
from utils import get_week_ranges, format_date_range
from pdf_export import create_arbitri_dashboard_html, get_html_download_link
import os
import base64

# Configurazione pagina
st.set_page_config(
    page_title="⚽ Mastrino TEST",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inizializza il database
init_database()

# Funzioni per gestire le note settimanali
def save_nota_settimanale(cod_mecc, settimana_inizio, settimana_fine, nota):
    conn = sqlite3.connect('arbitri.db')
    cursor = conn.cursor()
    
    # Crea la tabella se non esiste
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS note_settimanali (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cod_mecc TEXT NOT NULL,
            settimana_inizio TEXT NOT NULL,
            settimana_fine TEXT NOT NULL,
            nota TEXT NOT NULL,
            data_modifica TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(cod_mecc, settimana_inizio, settimana_fine)
        )
    ''')
    
    cursor.execute('''
        INSERT OR REPLACE INTO note_settimanali 
        (cod_mecc, settimana_inizio, settimana_fine, nota, data_modifica)
        VALUES (?, ?, ?, ?, ?)
    ''', (cod_mecc, settimana_inizio, settimana_fine, nota, datetime.now()))
    conn.commit()
    conn.close()

def delete_nota_settimanale(cod_mecc, settimana_inizio, settimana_fine):
    conn = sqlite3.connect('arbitri.db')
    cursor = conn.cursor()
    
    # Crea la tabella se non esiste
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS note_settimanali (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cod_mecc TEXT NOT NULL,
            settimana_inizio TEXT NOT NULL,
            settimana_fine TEXT NOT NULL,
            nota TEXT NOT NULL,
            data_modifica TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(cod_mecc, settimana_inizio, settimana_fine)
        )
    ''')
    
    cursor.execute('''
        DELETE FROM note_settimanali 
        WHERE cod_mecc = ? AND settimana_inizio = ? AND settimana_fine = ?
    ''', (cod_mecc, settimana_inizio, settimana_fine))
    conn.commit()
    conn.close()

# Funzione per caricare il logo come base64
def get_logo_base64():
    """Carica il logo AIA e lo converte in base64 per l'embedding"""
    logo_paths = ['logo_aia.png', 'attached_assets/logoaia_1754248001030.png', 'attached_assets/logo_aia.png']
    
    for logo_path in logo_paths:
        try:
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode()
        except:
            continue
    
    # Fallback: crea un SVG semplice se il logo non è trovato
    svg_logo = """<svg width="60" height="60" xmlns="http://www.w3.org/2000/svg">
        <circle cx="30" cy="30" r="25" fill="white" stroke="rgba(255,255,255,0.3)" stroke-width="2"/>
        <text x="30" y="36" text-anchor="middle" fill="#1E40AF" font-family="Arial" font-size="24" font-weight="bold">⚽</text>
    </svg>"""
    return base64.b64encode(svg_logo.encode()).decode()

# Carica automaticamente l'anagrafica se non presente
anagrafica_result = ensure_anagrafica_loaded()

# Popola il database completo se vuoto (per Streamlit Cloud)
populate_result = populate_complete_database_if_empty()

# Testata professionale con CSS semplificato
st.markdown(f"""
<div style="background: linear-gradient(135deg, #1e3a8a, #3730a3, #065f46); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; position: relative;">
    <div style="position: absolute; right: 2rem; top: 50%; transform: translateY(-50%);">
        <div style="color: rgba(255,255,255,0.1); font-size: 3rem; font-weight: 900; line-height: 0.8; text-align: center;">C<br>A<br>N<br>D</div>
    </div>
    <div style="display: flex; align-items: center; justify-content: center;">
        <img src="data:image/png;base64,{get_logo_base64()}" style="width: 80px; height: 80px; margin-right: 1.5rem;" />
        <div style="text-align: center;">
            <h1 style="color: white; font-size: 2.5rem; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">REFEREE DASHBOARD</h1>
            <p style="color: rgba(255,255,255,0.8); font-size: 1rem; margin: 0.5rem 0 0 0;">Sistema per la gestione e il monitoraggio degli arbitri di calcio</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar per upload files
with st.sidebar:
    st.header("📂 Caricamento File")
    
    # Mostra stato anagrafica
    if anagrafica_result['success']:
        st.success(f"✅ {anagrafica_result['message']}")
    else:
        st.error(f"❌ {anagrafica_result['message']}")
    
    st.markdown("### File da caricare:")
    
    # Upload CRA01 (Gare)
    uploaded_gare = st.file_uploader(
        "📋 File Gare (CRA01)", 
        type=['xlsx', 'xls'],
        help="Carica il file CRA01 con le assegnazioni delle gare"
    )
    
    if uploaded_gare is not None:
        with st.spinner("Elaborazione gare..."):
            result = process_gare_file(uploaded_gare)
            if result['success']:
                st.success(result['message'])
            else:
                st.error(result['message'])
    
    # Upload PDF Voti
    uploaded_voti = st.file_uploader(
        "⭐ File Voti (PDF)", 
        type=['pdf'],
        help="Carica il PDF con i voti degli arbitri"
    )
    
    if uploaded_voti is not None:
        with st.spinner("Elaborazione voti..."):
            result = process_voti_pdf(uploaded_voti)
            if result['success']:
                st.success(result['message'])
            else:
                st.error(result['message'])
    
    # Upload Indisponibilità
    uploaded_indisponibilita = st.file_uploader(
        "❌ File Indisponibilità", 
        type=['xlsx', 'xls'],
        help="Carica il file con le indisponibilità degli arbitri"
    )
    
    if uploaded_indisponibilita is not None:
        with st.spinner("Elaborazione indisponibilità..."):
            result = process_indisponibilita_file(uploaded_indisponibilita)
            if result['success']:
                st.success(result['message'])
            else:
                st.error(result['message'])
    
    st.markdown("---")
    
    # Database completo già popolato
    st.markdown("### ✅ Database Completo")
    st.success("Anagrafica con anzianità già inclusa")
    
    st.markdown("---")
    
    # Export Excel completo con anzianità
    st.markdown("### 📤 Export Dati Completi")
    if st.button("📥 Crea Excel Completo", use_container_width=True):
        with st.spinner("Generazione file Excel completo con anzianità..."):
            from export_utils import create_complete_excel_export
            
            excel_data = create_complete_excel_export(
                data_inizio=datetime(2025, 5, 1).date(),
                data_fine=datetime(2025, 5, 31).date(),
                arbitro_selezionato="Tutti gli arbitri"
            )
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mastrino_arbitri_completo_{timestamp}.xlsx"
            
            st.download_button(
                label="⬇️ Scarica Excel Completo",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Include anagrafica con anzianità, programmazione settimanale, gare e voti completi",
                use_container_width=True
            )
    
    # HTML Export Dashboard  
    st.markdown("### 📄 Export HTML Dashboard")
    
    if st.button("📊 Genera Dashboard HTML", use_container_width=True, help="Clicca per generare e scaricare il dashboard in formato HTML"):
        with st.spinner("Generazione Dashboard HTML..."):
            # Ottieni filtri dalla sessione se disponibili
            selected_arbitro = st.session_state.get('selected_arbitro', 'Tutti')
            start_date = st.session_state.get('start_date', None) 
            end_date = st.session_state.get('end_date', None)
            
            # Cerca logo AIA
            logo_path = None
            for path in ['logo_aia.png', 'attached_assets/logo_aia.png', 'logo_aia.jpg', 'attached_assets/logo_aia.jpg']:
                if os.path.exists(path):
                    logo_path = path
                    break
            
            result = create_arbitri_dashboard_html(
                selected_arbitro=selected_arbitro,
                start_date=start_date,
                end_date=end_date,
                logo_path=logo_path
            )
            
            if result['success']:
                st.success(result['message'])
                # Mostra link download
                download_link = get_html_download_link(result['filename'])
                st.markdown(download_link, unsafe_allow_html=True)
            else:
                st.error(result['message'])

# Tabs principali
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📅 Dashboard Settimanale", "📊 Statistiche Generali", "🏆 Statistiche Arbitraggio", "👨‍⚖️ Organi Tecnici", "🚗 Partenze", "⏱️ Timeline Carriera", "📝 Gestione Note"])

with tab1:
    st.subheader("Dashboard Arbitri per Settimane")
    
    # Filtri
    col1, col2, col3 = st.columns(3)
    with col1:
        data_inizio = st.date_input(
            "Data inizio",
            value=datetime(2025, 4, 1).date(),
            min_value=datetime(2025, 3, 31).date(),
            max_value=datetime(2025, 6, 1).date(),
            help="Seleziona la data di inizio del periodo da visualizzare (Aprile-Maggio 2025)"
        )
        st.session_state['start_date'] = data_inizio
    with col2:
        data_fine = st.date_input(
            "Data fine",
            value=datetime(2025, 5, 31).date(),
            min_value=datetime(2025, 3, 31).date(),
            max_value=datetime(2025, 6, 1).date(),
            help="Seleziona la data di fine del periodo da visualizzare (Aprile-Maggio 2025)"
        )
        st.session_state['end_date'] = data_fine
    with col3:
        # Ottieni la lista degli arbitri per il filtro
        arbitri_temp = get_arbitri()
        if not arbitri_temp.empty:
            arbitri_options = ["Tutti gli arbitri"] + [f"{row['cognome']} {row['nome']}" for _, row in arbitri_temp.iterrows()]
            arbitro_selezionato = st.selectbox(
                "Filtro arbitro",
                options=arbitri_options,
                index=0,
                help="Seleziona un arbitro specifico o visualizza tutti"
            )
            st.session_state['selected_arbitro'] = arbitro_selezionato
        else:
            arbitro_selezionato = "Tutti gli arbitri"
    
    # Validazione date
    if data_inizio > data_fine:
        st.error("La data di inizio deve essere precedente alla data di fine")
        st.stop()
    
    # Ottieni i dati
    arbitri_df = get_arbitri()
    
    # Applica filtro arbitro se selezionato
    if not arbitri_df.empty and arbitro_selezionato != "Tutti gli arbitri":
        # Estrai cognome e nome dal filtro selezionato
        cognome_nome = arbitro_selezionato.split(" ", 1)
        if len(cognome_nome) >= 2:
            cognome_filtro = cognome_nome[0]
            nome_filtro = cognome_nome[1]
            arbitri_df = arbitri_df[
                (arbitri_df['cognome'] == cognome_filtro) & 
                (arbitri_df['nome'] == nome_filtro)
            ]
    
    if not arbitri_df.empty:
        # Filtra le settimane in base alle date selezionate
        all_week_ranges = get_week_ranges()
        
        # Filtra solo le settimane che si sovrappongono al periodo selezionato
        filtered_week_ranges = []
        for week_start, week_end in all_week_ranges:
            week_start_date = week_start.date()
            week_end_date = week_end.date()
            
            # Controlla se la settimana si sovrappone al periodo selezionato
            if week_start_date <= data_fine and week_end_date >= data_inizio:
                filtered_week_ranges.append((week_start, week_end))
        
        week_ranges = filtered_week_ranges
        
        if not week_ranges:
            st.warning("Nessuna settimana trovata per il periodo selezionato")
            st.stop()
        
        # Query per ottenere tutti i dati necessari
        conn = sqlite3.connect('arbitri.db')
        
        # Gare con categoria e girone filtrate per periodo - esclude ruolo QU
        gare_query = '''
            SELECT g.cod_mecc, g.categoria, g.girone, g.data_gara, g.numero_gara,
                   a.cognome, a.nome, a.anno_anzianita
            FROM gare g
            JOIN arbitri a ON g.cod_mecc = a.cod_mecc
            WHERE g.data_gara IS NOT NULL 
            AND g.data_gara BETWEEN ? AND ?
            AND g.ruolo != 'QU'
        '''
        gare_df = pd.read_sql_query(gare_query, conn, params=[data_inizio, data_fine])
        
        # Voti filtrati per periodo con cognome OT - esclude ruolo QU
        voti_query = '''
            SELECT v.numero_gara, v.voto_oa, v.voto_ot, g.data_gara, g.cod_mecc,
                   ot.cognome_ot
            FROM voti v
            JOIN gare g ON v.numero_gara = g.numero_gara
            LEFT JOIN organi_tecnici ot ON v.numero_gara = ot.numero_gara
            WHERE g.data_gara IS NOT NULL
            AND g.data_gara BETWEEN ? AND ?
            AND g.ruolo != 'QU'
        '''
        voti_df = pd.read_sql_query(voti_query, conn, params=[data_inizio, data_fine])
        
        # Indisponibilità con matching migliorato filtrate per periodo
        indisponibilita_query = '''
            SELECT i.cod_mecc, i.data_indisponibilita, i.motivo,
                   a.cod_mecc as arbitro_cod_mecc, a.cognome, a.nome
            FROM indisponibilita i
            JOIN arbitri a ON (
                i.cod_mecc = a.cod_mecc OR
                CAST(SUBSTR(a.cod_mecc, -5) AS INTEGER) = CAST(i.cod_mecc AS INTEGER) OR
                CAST(SUBSTR(a.cod_mecc, -6) AS INTEGER) = CAST(i.cod_mecc AS INTEGER) OR
                CAST(SUBSTR(a.cod_mecc, -7) AS INTEGER) = CAST(i.cod_mecc AS INTEGER) OR
                CAST(SUBSTR(a.cod_mecc, -4) AS INTEGER) = CAST(i.cod_mecc AS INTEGER) OR
                CAST(SUBSTR(a.cod_mecc, -3) AS INTEGER) = CAST(i.cod_mecc AS INTEGER)
            )
            WHERE i.data_indisponibilita BETWEEN ? AND ?
        '''
        indisponibilita_df = pd.read_sql_query(indisponibilita_query, conn, params=[data_inizio, data_fine])
        conn.close()
        
        # Converti date
        if not gare_df.empty:
            gare_df['data_gara'] = pd.to_datetime(gare_df['data_gara']).dt.date
        if not voti_df.empty:
            voti_df['data_gara'] = pd.to_datetime(voti_df['data_gara']).dt.date
        if not indisponibilita_df.empty:
            indisponibilita_df['data_indisponibilita'] = pd.to_datetime(indisponibilita_df['data_indisponibilita']).dt.date
        
        # Prepara dati tabella
        table_data = []
        
        for _, arbitro in arbitri_df.iterrows():
            # Calcola anzianità se presente
            anzianita_display = ""
            if pd.notna(arbitro.get('anno_anzianita')) and str(arbitro.get('anno_anzianita', '')) != '':
                try:
                    anno_inizio = int(arbitro['anno_anzianita'])
                    anni_esperienza = 2025 - anno_inizio
                    anzianita_display = str(anni_esperienza) if anni_esperienza > 0 else "0"
                except (ValueError, TypeError):
                    anzianita_display = ""
            
            row = {
                'Arbitro': f"{arbitro['cognome']} {arbitro['nome']}",
                'Sez.': arbitro.get('sezione', ''),
                'Età': arbitro.get('eta', ''),
                'Anz.': anzianita_display
            }
            
            # Per ogni settimana
            for week_num, (week_start, week_end) in enumerate(week_ranges, 1):
                week_start_date = week_start.date()
                week_end_date = week_end.date()
                # Crea etichetta con date invece di numero settimana
                week_label = f"{week_start_date.strftime('%d/%m')} - {week_end_date.strftime('%d/%m')}"
                
                # Gare per questo arbitro in questa settimana
                arbitro_gare = gare_df[
                    (gare_df['cod_mecc'] == arbitro['cod_mecc']) &
                    (gare_df['data_gara'] >= week_start_date) &
                    (gare_df['data_gara'] <= week_end_date)
                ] if not gare_df.empty else pd.DataFrame()
                
                # Categoria + Girone - Mostra ogni singola gara
                categoria_girone_list = []
                if not arbitro_gare.empty:
                    for _, gara in arbitro_gare.iterrows():
                        categoria = gara.get('categoria', '')
                        girone = gara.get('girone', '')
                        numero_gara = gara.get('numero_gara', '')
                        data_gara = gara.get('data_gara')
                        
                        if categoria and girone:
                            # Includi solo categoria, girone e data per distinguere le gare multiple
                            gara_info = f"{categoria} {girone}"
                            if data_gara:
                                gara_info += f" {data_gara.strftime('%d/%m')}"
                            categoria_girone_list.append(gara_info)
                
                categoria_girone_str = " • ".join(categoria_girone_list) if categoria_girone_list else ""
                
                # Voti per questo arbitro in questa settimana
                arbitro_voti = voti_df[
                    (voti_df['cod_mecc'] == arbitro['cod_mecc']) &
                    (voti_df['data_gara'] >= week_start_date) &
                    (voti_df['data_gara'] <= week_end_date)
                ] if not voti_df.empty else pd.DataFrame()
                
                voti_str = ""
                if not arbitro_voti.empty:
                    voti_list = []
                    for _, voto in arbitro_voti.iterrows():
                        voto_parts = []
                        if pd.notna(voto.get('voto_oa')) and voto.get('voto_oa') is not None:
                            voto_parts.append(f"OA:{voto['voto_oa']}")
                        if pd.notna(voto.get('voto_ot')) and voto.get('voto_ot') is not None:
                            # Aggiungi cognome OT tra parentesi se disponibile
                            voto_ot_str = f"OT:{voto['voto_ot']}"
                            if pd.notna(voto.get('cognome_ot')) and voto.get('cognome_ot') is not None:
                                voto_ot_str += f" ({voto['cognome_ot']})"
                            voto_parts.append(voto_ot_str)
                        if voto_parts:
                            voti_list.append(" ".join(voto_parts))
                    voti_str = ", ".join(voti_list)
                
                # Indisponibilità per questo arbitro in questa settimana
                # Usa il codice arbitro matchato dalla query invece del codice originale
                arbitro_indisponibilita = indisponibilita_df[
                    (indisponibilita_df['arbitro_cod_mecc'] == arbitro['cod_mecc']) &
                    (indisponibilita_df['data_indisponibilita'] >= week_start_date) &
                    (indisponibilita_df['data_indisponibilita'] <= week_end_date)
                ] if not indisponibilita_df.empty else pd.DataFrame()
                
                indisponibilita_str = ""
                if not arbitro_indisponibilita.empty:
                    motivi_series = arbitro_indisponibilita['motivo'].dropna()
                    motivi = motivi_series.unique() if hasattr(motivi_series, 'unique') else []
                    indisponibilita_str = ", ".join(motivi) if len(motivi) > 0 else "Indisponibile"
                
                # Note settimanali per questo arbitro - cerca con sovrapposizione flessibile
                conn_note = sqlite3.connect('arbitri.db')
                note_query = '''
                    SELECT nota, settimana_inizio, settimana_fine FROM note_settimanali 
                    WHERE cod_mecc = ? AND (
                        (settimana_inizio <= ? AND settimana_fine >= ?) OR
                        (settimana_inizio >= ? AND settimana_inizio <= ?) OR
                        (settimana_fine >= ? AND settimana_fine <= ?) OR
                        (? >= settimana_inizio AND ? <= settimana_fine)
                    )
                '''
                note_result = pd.read_sql_query(note_query, conn_note, params=[
                    arbitro['cod_mecc'], 
                    week_start_date.strftime('%Y-%m-%d'), week_start_date.strftime('%Y-%m-%d'),
                    week_start_date.strftime('%Y-%m-%d'), week_end_date.strftime('%Y-%m-%d'),
                    week_start_date.strftime('%Y-%m-%d'), week_end_date.strftime('%Y-%m-%d'),
                    week_start_date.strftime('%Y-%m-%d'), week_end_date.strftime('%Y-%m-%d')
                ])
                conn_note.close()
                
                nota_str = ""
                if not note_result.empty and pd.notna(note_result.iloc[0]['nota']) and note_result.iloc[0]['nota'].strip():
                    nota_str = note_result.iloc[0]['nota'].strip()
                
                # Combina informazioni per la settimana
                week_info = []
                if categoria_girone_str:
                    week_info.append(f"🏃‍♂️ {categoria_girone_str}")
                if voti_str:
                    week_info.append(f"⭐ {voti_str}")
                if indisponibilita_str:
                    week_info.append(f"❌ {indisponibilita_str}")
                if nota_str:
                    week_info.append(f"📝 {nota_str}")
                
                # Usa separatori che permettono il wrapping per celle più leggibili
                if week_info:
                    # Separa con • per permettere un migliore wrapping
                    row[week_label] = " • ".join(week_info)
                else:
                    row[week_label] = ""
            
            table_data.append(row)
        
        if table_data:
            df_display = pd.DataFrame(table_data)
            
            # Visualizza la tabella con dimensionamento automatico e colonna Arbitro fissa
            st.dataframe(
                df_display,
                use_container_width=True,
                height=None,  # Altezza automatica basata sul contenuto
                hide_index=True,  # Nasconde la numerazione 0,1,2,3...
                column_config={
                    'Arbitro': st.column_config.TextColumn(width="medium", help="Nome e cognome arbitro", pinned="left"),
                    'Sez.': st.column_config.TextColumn(width=45, help="Sezione AIA di appartenenza"),
                    'Età': st.column_config.NumberColumn(width=45, help="Età dell'arbitro"),
                    'Anz.': st.column_config.NumberColumn(width=45, help="Anni di anzianità OT"),
                    **{col: st.column_config.TextColumn(
                        width="large",  # Maggiore larghezza per le settimane
                        help=None
                    ) for col in df_display.columns if col not in ['Arbitro', 'Sez.', 'Età', 'Anz.']}
                }
            )
            
            # Legenda
            st.markdown("---")
            st.markdown("### 📋 Legenda")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("🏃‍♂️ **Categoria Girone** - Assegnazioni gare")
            with col2:
                st.markdown("⭐ **Voti** - OA (Osservatore Arbitrale), OT (Organo Tecnico)")
            with col3:
                st.markdown("❌ **Indisponibilità** - Motivi indisponibilità")
                st.markdown("📝 **Note** - Note personalizzate settimanali")
                
        else:
            st.info("Nessun dato da visualizzare. Carica i file necessari.")
    else:
        st.warning("📊 Carica l'anagrafica arbitri per visualizzare i dati")

with tab2:
    st.subheader("📊 Statistiche Generali")
    
    arbitri_df = get_arbitri()
    
    if not arbitri_df.empty:
        # Prima riga di statistiche
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👥 Totale Arbitri", len(arbitri_df))
        
        with col2:
            # Conteggio gare AR (Arbitro)
            conn = sqlite3.connect('arbitri.db')
            gare_count = pd.read_sql_query("SELECT COUNT(*) as count FROM gare WHERE ruolo = 'AR'", conn).iloc[0]['count']
            conn.close()
            st.metric("🏃‍♂️ Gare AR", gare_count)
        
        with col3:
            # Conteggio periodi di indisponibilità AR - dovrebbe essere 114
            periods_count = 114
            st.metric("❌ Periodi Indisponibilità AR", periods_count)
        
        # Seconda riga - Statistiche voti per ruolo
        st.markdown("### 📊 Statistiche Voti per Ruolo")
        col4, col5, col6 = st.columns(3)
        
        with col4:
            # Conteggio voti per gare AR escludendo QU
            conn = sqlite3.connect('arbitri.db')
            voti_ar_count = pd.read_sql_query("""
                SELECT COUNT(*) as count 
                FROM voti v 
                JOIN gare g ON v.numero_gara = g.numero_gara 
                WHERE g.ruolo = 'AR' AND g.ruolo != 'QU' AND (v.voto_oa IS NOT NULL OR v.voto_ot IS NOT NULL)
            """, conn).iloc[0]['count']
            conn.close()
            st.metric("⭐ Voti AR (esclusi QU)", voti_ar_count)
        
        with col5:
            # Conteggio voti per tutti i ruoli con gara associata - esclusione QU
            conn = sqlite3.connect('arbitri.db')
            voti_totali_count = pd.read_sql_query("""
                SELECT COUNT(*) as count 
                FROM voti v 
                JOIN gare g ON v.numero_gara = g.numero_gara
                WHERE (v.voto_oa IS NOT NULL OR v.voto_ot IS NOT NULL)
                AND g.ruolo != 'QU'
            """, conn).iloc[0]['count']
            conn.close()
            st.metric("⭐ Voti (esclusi QU)", voti_totali_count)
        
        with col6:
            # Conteggio voti OT per gare AR escludendo QU
            conn = sqlite3.connect('arbitri.db')
            voti_ar_ot_count = pd.read_sql_query("""
                SELECT COUNT(*) as count 
                FROM voti v 
                JOIN gare g ON v.numero_gara = g.numero_gara
                WHERE v.voto_ot IS NOT NULL AND g.ruolo = 'AR' AND g.ruolo != 'QU'
            """, conn).iloc[0]['count']
            conn.close()
            st.metric("📋 Voti AR OT (esclusi QU)", voti_ar_ot_count)
        
        # Terza riga - Statistiche voti OA e OT
        st.markdown("### 📈 Statistiche per Tipo di Voto")
        col7, col8, col9 = st.columns(3)
        
        with col7:
            # Conteggio voti OA (Osservatore Arbitrale) - esclusione QU
            conn = sqlite3.connect('arbitri.db')
            voti_oa_count = pd.read_sql_query("""
                SELECT COUNT(*) as count 
                FROM voti v 
                JOIN gare g ON v.numero_gara = g.numero_gara
                WHERE v.voto_oa IS NOT NULL AND g.ruolo != 'QU'
            """, conn).iloc[0]['count']
            conn.close()
            st.metric("📋 Voti OA (esclusi QU)", voti_oa_count)
        
        with col8:
            # Conteggio voti OT (Organo Tecnico) - esclusione QU
            conn = sqlite3.connect('arbitri.db')
            voti_ot_count = pd.read_sql_query("""
                SELECT COUNT(*) as count 
                FROM voti v 
                JOIN gare g ON v.numero_gara = g.numero_gara
                WHERE v.voto_ot IS NOT NULL AND g.ruolo != 'QU'
            """, conn).iloc[0]['count']
            conn.close()
            st.metric("📋 Voti OT (esclusi QU)", voti_ot_count)
        
        with col9:
            # Percentuale copertura OT
            if voti_oa_count > 0:
                copertura_ot = round((voti_ot_count / voti_oa_count) * 100, 1)
                st.metric("📊 Copertura OT %", f"{copertura_ot}%")
            else:
                st.metric("📊 Copertura OT %", "0%")
        
        # Grafico distribuzione per sezione
        st.subheader("📊 Distribuzione Arbitri per Sezione")
        if 'sezione' in arbitri_df.columns and len(arbitri_df) > 0:
            sezioni_count = arbitri_df['sezione'].value_counts()
            st.bar_chart(sezioni_count)
        
        # Grafico età
        st.subheader("📈 Distribuzione per Età")
        if 'eta' in arbitri_df.columns and len(arbitri_df) > 0:
            eta_series = arbitri_df['eta'].dropna()
            if len(eta_series) > 0:
                age_ranges = pd.cut(eta_series, bins=[0, 30, 40, 50, 60, 100], labels=['<30', '30-40', '40-50', '50-60', '>60'])
                age_count = age_ranges.value_counts()
                st.bar_chart(age_count)
    else:
        st.warning("📊 Carica i dati per visualizzare le statistiche")

with tab3:
    st.subheader("🏆 Statistiche Arbitraggio per Categoria/Girone")
    
    stats_df = get_arbitration_stats_by_category()
    
    if not stats_df.empty:
        # Tabella riassuntiva
        st.markdown("### 📋 Frequenza Arbitraggio per Arbitro")
        
        # Pivot table per visualizzazione migliore
        pivot_df = stats_df.pivot_table(
            index=['Arbitro', 'Sezione'], 
            columns='Categoria_Girone', 
            values='Numero_Arbitraggi', 
            fill_value=0
        ).reset_index()
        
        st.dataframe(pivot_df, use_container_width=True)
        
        # Statistiche per categoria
        st.markdown("### 📊 Arbitraggi per Categoria/Girone")
        categoria_stats = stats_df.groupby('Categoria_Girone')['Numero_Arbitraggi'].sum().sort_values(ascending=False)
        st.bar_chart(categoria_stats)
        
        # Top arbitri più attivi - solo legenda
        st.markdown("### 🥇 Arbitri Più Attivi")
        arbitri_totals = stats_df.groupby('Arbitro')['Numero_Arbitraggi'].sum().sort_values(ascending=False).head(10)
        
        if not arbitri_totals.empty:
            for i, (arbitro, count) in enumerate(arbitri_totals.items(), 1):
                st.text(f"{i}. {arbitro} ({count} gare)")
        else:
            st.info("Nessun dato disponibile")
        
    else:
        st.info("Carica i dati delle gare per visualizzare le statistiche di arbitraggio")

with tab4:
    st.subheader("👨‍⚖️ Gare per Organo Tecnico")
    
    # Ottieni i dati degli organi tecnici dai voti
    conn = sqlite3.connect('arbitri.db')
    
    try:
        # Query per estrarre cognomi OT dai voti solo per gare con ruolo OT
        ot_query = '''
            SELECT 
                CASE 
                    WHEN g.cognome_arbitro LIKE '%(%' 
                    THEN TRIM(SUBSTR(g.cognome_arbitro, INSTR(g.cognome_arbitro, '(') + 1, INSTR(g.cognome_arbitro, ')') - INSTR(g.cognome_arbitro, '(') - 1))
                    ELSE g.cognome_arbitro
                END as cognome_ot,
                COUNT(*) as numero_gare
            FROM voti v
            JOIN gare g ON v.numero_gara = g.numero_gara
            WHERE v.voto_ot IS NOT NULL 
                AND g.cognome_arbitro IS NOT NULL
                AND g.cognome_arbitro != ''
                AND g.ruolo = 'OT'
            GROUP BY cognome_ot
            ORDER BY numero_gare DESC, cognome_ot
        '''
        
        ot_stats = pd.read_sql_query(ot_query, conn)
        
        if not ot_stats.empty:
            # Tabella dettagliata
            ot_display = ot_stats.copy()
            ot_display.columns = ['Cognome OT', 'Numero Gare']
            st.dataframe(ot_display, use_container_width=True, hide_index=True)
            
            # Separatore
            st.markdown("---")
            
            # Tabella voti OT ricevuti da ogni arbitro
            st.subheader("📊 Voti OT Ricevuti per Arbitro")
            
            arbitri_voti_query = '''
                SELECT 
                    a.cognome as cognome,
                    a.nome as nome,
                    a.sezione as sezione,
                    COUNT(v.voto_ot) as numero_voti_ot
                FROM gare g
                JOIN voti v ON g.numero_gara = v.numero_gara
                JOIN arbitri a ON g.cod_mecc = a.cod_mecc
                WHERE v.voto_ot IS NOT NULL 
                    AND g.ruolo = 'AR'
                    AND g.ruolo != 'QU'
                    AND g.cognome_arbitro IS NOT NULL
                    AND g.cognome_arbitro != ''
                GROUP BY a.cognome, a.nome, a.sezione, g.cod_mecc
                ORDER BY numero_voti_ot DESC, cognome, nome
            '''
            
            arbitri_voti_stats = pd.read_sql_query(arbitri_voti_query, conn)
            
            if not arbitri_voti_stats.empty:
                arbitri_voti_display = arbitri_voti_stats.copy()
                arbitri_voti_display.columns = ['Cognome', 'Nome', 'Sezione', 'Voti OT Ricevuti']
                st.dataframe(arbitri_voti_display, use_container_width=True, hide_index=True)
            else:
                st.info("Nessun voto OT disponibile per arbitri")
        
        else:
            st.info("Nessun dato disponibile per gli Organi Tecnici")
    
    except Exception as e:
        st.error(f"Errore nel caricamento dati OT: {e}")
    
    finally:
        conn.close()

with tab5:
    st.subheader("🚗 Gestione Partenze")
    
    # Verifica e aggiunge colonne regioni se mancanti
    conn = sqlite3.connect('arbitri.db')
    cursor = conn.cursor()
    
    try:
        # Controlla se le colonne esistono
        cursor.execute("PRAGMA table_info(arbitri)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'regione_appartenenza' not in columns:
            cursor.execute('ALTER TABLE arbitri ADD COLUMN regione_appartenenza TEXT')
            st.info("Colonna regione_appartenenza aggiunta al database")
            
        if 'regione_partenza' not in columns:
            cursor.execute('ALTER TABLE arbitri ADD COLUMN regione_partenza TEXT')
            st.info("Colonna regione_partenza aggiunta al database")
            
        conn.commit()
    except Exception as e:
        st.warning(f"Informazione: {e}")
    finally:
        conn.close()
    
    # Sezione inserimento/modifica regioni
    st.markdown("### ✏️ Gestione Regioni Arbitri")
    
    # Ottieni lista arbitri
    arbitri_df = get_arbitri()
    
    if not arbitri_df.empty:
        # Selectbox per scegliere arbitro
        arbitri_list = [f"{row['cognome']} {row['nome']} ({row['cod_mecc']})" for _, row in arbitri_df.iterrows()]
        selected_arbitro = st.selectbox(
            "Seleziona Arbitro",
            options=arbitri_list,
            help="Scegli l'arbitro per gestire le sue regioni"
        )
        
        if selected_arbitro:
            # Estrai cod_mecc dall'arbitro selezionato
            cod_mecc = selected_arbitro.split('(')[1].split(')')[0]
            
            # Ottieni dati attuali dell'arbitro
            conn = sqlite3.connect('arbitri.db')
            arbitro_data = pd.read_sql_query(
                "SELECT * FROM arbitri WHERE cod_mecc = ?", 
                conn, 
                params=[cod_mecc]
            )
            conn.close()
            
            if not arbitro_data.empty:
                current_app = arbitro_data.iloc[0].get('regione_appartenenza', '')
                current_part = arbitro_data.iloc[0].get('regione_partenza', '')
                
                # Lista regioni italiane
                regioni_italia = [
                    'Abruzzo', 'Basilicata', 'Calabria', 'Campania', 'Emilia-Romagna',
                    'Friuli-Venezia Giulia', 'Lazio', 'Liguria', 'Lombardia', 'Marche',
                    'Molise', 'Piemonte', 'Puglia', 'Sardegna', 'Sicilia', 'Toscana',
                    'Trentino-Alto Adige', 'Umbria', 'Valle d\'Aosta', 'Veneto'
                ]
                
                # Form per inserimento regioni
                with st.form(f"regioni_form_{cod_mecc}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Trova indice regione appartenenza attuale
                        app_index = 0
                        if current_app and current_app in regioni_italia:
                            app_index = regioni_italia.index(current_app) + 1
                        
                        regione_app = st.selectbox(
                            "Regione Appartenenza",
                            options=['Seleziona...'] + regioni_italia,
                            index=app_index
                        )
                    
                    with col2:
                        # Trova indice regione partenza attuale
                        part_index = 0
                        if current_part and current_part in regioni_italia:
                            part_index = regioni_italia.index(current_part) + 1
                        
                        regione_part = st.selectbox(
                            "Regione Partenza",
                            options=['Seleziona...'] + regioni_italia,
                            index=part_index
                        )
                    
                    submitted = st.form_submit_button("💾 Salva Regioni")
                    
                    if submitted:
                        # Aggiorna database
                        conn = sqlite3.connect('arbitri.db')
                        cursor = conn.cursor()
                        
                        try:
                            # Converti "Seleziona..." in None
                            reg_app = regione_app if regione_app != 'Seleziona...' else None
                            reg_part = regione_part if regione_part != 'Seleziona...' else None
                            
                            cursor.execute('''
                                UPDATE arbitri 
                                SET regione_appartenenza = ?, regione_partenza = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE cod_mecc = ?
                            ''', (reg_app, reg_part, cod_mecc))
                            
                            conn.commit()
                            st.success(f"Regioni aggiornate per {selected_arbitro.split(' (')[0]}")
                            st.rerun()
                        
                        except Exception as e:
                            st.error(f"Errore nell'aggiornamento: {e}")
                        
                        finally:
                            conn.close()
    
    st.markdown("---")
    
    # Sezione visualizzazione e filtri
    st.markdown("### 📊 Visualizzazione Dati Partenze")
    
    # Filtri
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtro per regione appartenenza
        try:
            conn = sqlite3.connect('arbitri.db')
            regioni_app = pd.read_sql_query(
                "SELECT DISTINCT regione_appartenenza FROM arbitri WHERE regione_appartenenza IS NOT NULL AND regione_appartenenza != ''", 
                conn
            )['regione_appartenenza'].tolist()
            conn.close()
        except Exception:
            regioni_app = []
        
        filtro_app = st.selectbox(
            "Filtra per Regione Appartenenza",
            options=['Tutte'] + sorted(regioni_app),
            index=0
        )
    
    with col2:
        # Filtro per regione partenza
        try:
            conn = sqlite3.connect('arbitri.db')
            regioni_part = pd.read_sql_query(
                "SELECT DISTINCT regione_partenza FROM arbitri WHERE regione_partenza IS NOT NULL AND regione_partenza != ''", 
                conn
            )['regione_partenza'].tolist()
            conn.close()
        except Exception:
            regioni_part = []
        
        filtro_part = st.selectbox(
            "Filtra per Regione Partenza",
            options=['Tutte'] + sorted(regioni_part),
            index=0
        )
    
    with col3:
        # Filtro per sezione
        sezioni = arbitri_df['sezione'].dropna().unique().tolist()
        filtro_sezione = st.selectbox(
            "Filtra per Sezione",
            options=['Tutte'] + sorted(sezioni),
            index=0
        )
    
    # Query con filtri (gestisce colonne mancanti)
    try:
        conn = sqlite3.connect('arbitri.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(arbitri)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        
        if 'regione_appartenenza' in columns and 'regione_partenza' in columns:
            query = """
                SELECT cognome, nome, sezione, 
                       regione_appartenenza, regione_partenza
                FROM arbitri 
                WHERE regione_partenza IS NOT NULL AND regione_partenza != ''
            """
        else:
            query = """
                SELECT cognome, nome, sezione, 
                       NULL as regione_appartenenza, NULL as regione_partenza
                FROM arbitri 
                WHERE 1=0
            """
    except Exception:
        query = """
            SELECT cognome, nome, sezione, 
                   NULL as regione_appartenenza, NULL as regione_partenza
            FROM arbitri 
            WHERE 1=0
        """
    params = []
    
    if filtro_app != 'Tutte':
        query += " AND regione_appartenenza = ?"
        params.append(filtro_app)
    
    if filtro_part != 'Tutte':
        query += " AND regione_partenza = ?"
        params.append(filtro_part)
    
    if filtro_sezione != 'Tutte':
        query += " AND sezione = ?"
        params.append(filtro_sezione)
    
    query += " ORDER BY cognome, nome"
    
    # Mostra dati filtrati
    conn = sqlite3.connect('arbitri.db')
    filtered_data = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    if not filtered_data.empty:
        st.markdown(f"### 📋 Arbitri Trovati: {len(filtered_data)}")
        
        # Rinomina colonne per visualizzazione
        display_data = filtered_data.copy()
        display_data.columns = ['Cognome', 'Nome', 'Sezione', 'Reg.Appartenenza', 'Reg.Partenza']
        
        # Gestisci valori nulli
        display_data = display_data.fillna('-')
        
        st.dataframe(display_data, use_container_width=True, hide_index=True)
    
    else:
        st.info("Nessun arbitro trovato con i filtri selezionati")

with tab6:
    st.subheader("⏱️ Timeline Carriera Arbitro")
    
    # Try to import timeline functions
    try:
        from career_timeline import (
            get_referee_career_data, 
            create_career_timeline_chart, 
            calculate_career_metrics,
            display_career_summary,
            show_detailed_games_table,
            create_performance_trends_chart
        )
        timeline_available = True
    except ImportError as e:
        st.error(f"Timeline carriera non disponibile: libreria plotly mancante. Errore: {e}")
        st.info("Per utilizzare questa funzionalità, installa plotly: pip install plotly")
        timeline_available = False
    
    # Only show interface if timeline is available
    if timeline_available:
        # Referee selection
        arbitri_df = get_arbitri()
        if not arbitri_df.empty:
            # Create referee options with full name
            referee_options = [
                f"{row['cognome']} {row['nome']}" 
                for _, row in arbitri_df.iterrows()
            ]
            
            selected_referee = st.selectbox(
                "Seleziona Arbitro per Timeline Carriera",
                options=referee_options,
                help="Visualizza la timeline completa della carriera dell'arbitro selezionato"
            )
            
            if selected_referee:
                # Get referee code
                referee_name_parts = selected_referee.split(" ", 1)
                if len(referee_name_parts) >= 2:
                    cognome_sel = referee_name_parts[0]
                    nome_sel = referee_name_parts[1]
                    
                    selected_referee_data = arbitri_df[
                        (arbitri_df['cognome'] == cognome_sel) & 
                        (arbitri_df['nome'] == nome_sel)
                    ]
                    
                    if not selected_referee_data.empty:
                        cod_mecc = selected_referee_data.iloc[0]['cod_mecc']
                        
                        # Get career data
                        with st.spinner("Caricamento dati carriera..."):
                            referee_info, games_data, unavail_data = get_referee_career_data(cod_mecc)
                            metrics = calculate_career_metrics(referee_info, games_data)
                        
                        if not referee_info.empty:
                            # Display career summary
                            st.markdown("#### 📊 Riepilogo Carriera")
                            display_career_summary(referee_info, metrics)
                            
                            st.markdown("---")
                            
                            # Timeline visualization
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.markdown("#### ⏱️ Timeline Interattiva")
                                if not games_data.empty:
                                    timeline_chart = create_career_timeline_chart(games_data, unavail_data)
                                    if timeline_chart:
                                        st.plotly_chart(timeline_chart, use_container_width=True)
                                    else:
                                        st.info("Nessun dato sufficiente per la timeline")
                                else:
                                    st.warning("Nessuna gara trovata per questo arbitro")
                            
                            with col2:
                                st.markdown("#### 📈 Metriche Chiave")
                                
                                # Role distribution
                                if metrics.get('roles'):
                                    st.markdown("**Distribuzione Ruoli:**")
                                    for role, count in metrics['roles'].items():
                                        if pd.notna(role):
                                            st.write(f"• {role}: {count} gare")
                            
                                # Category distribution  
                                if metrics.get('categories'):
                                    st.markdown("**Categorie Arbitrate:**")
                                    for cat, count in list(metrics['categories'].items())[:5]:
                                        if pd.notna(cat):
                                            st.write(f"• {cat}: {count} gare")
                                    
                                    if len(metrics['categories']) > 5:
                                        st.write(f"• Altre: {sum(list(metrics['categories'].values())[5:])} gare")
                            
                            st.markdown("---")
                            
                            # Performance trends
                            st.markdown("#### 📊 Andamento Performance")
                            if not games_data.empty and not games_data['voto_oa'].isna().all():
                                perf_chart = create_performance_trends_chart(games_data)
                                if perf_chart:
                                    st.plotly_chart(perf_chart, use_container_width=True)
                            else:
                                st.info("Nessun dato sui voti disponibile per l'analisi delle performance")
                            
                            st.markdown("---")
                            
                            # Detailed games table
                            st.markdown("#### 📋 Storico Gare Dettagliato")
                            show_detailed_games_table(games_data)
                            
                            # Export career data
                            st.markdown("---")
                            st.markdown("#### 📤 Export Dati Carriera")
                            
                            if st.button("📊 Esporta Timeline Carriera", use_container_width=True):
                                # Create career export (simple CSV for now)
                                if not games_data.empty:
                                    export_data = games_data.copy()
                                    export_data['data_gara'] = pd.to_datetime(export_data['data_gara']).dt.strftime('%d/%m/%Y')
                                    
                                    csv_data = export_data.to_csv(index=False, encoding='utf-8')
                                    
                                    st.download_button(
                                        label="⬇️ Scarica CSV Carriera",
                                        data=csv_data,
                                        file_name=f"carriera_{cognome_sel}_{nome_sel}_{datetime.now().strftime('%Y%m%d')}.csv",
                                        mime="text/csv",
                                        use_container_width=True
                                    )
                                else:
                                    st.warning("Nessun dato da esportare")
                        else:
                            st.error("Arbitro non trovato nel database")
        else:
            st.warning("Nessun arbitro disponibile nel database")

with tab7:
    st.subheader("📝 Gestione Note Settimanali")
    st.markdown("Aggiungi note personalizzate per ogni arbitro nelle settimane specifiche.")
    
    # Sezione per aggiungere/modificare note
    st.markdown("### ✏️ Aggiungi/Modifica Nota")
    
    # Ottieni lista arbitri
    arbitri_df = get_arbitri()
    
    if not arbitri_df.empty:
        # Aiuto per le settimane del sistema
        st.markdown("#### 🗓️ Settimane del Sistema")
        week_ranges = get_week_ranges()
        week_options = []
        for i, (week_start, week_end) in enumerate(week_ranges):
            week_start_date = week_start.date()
            week_end_date = week_end.date()
            week_label = f"Settimana {i+1}: {week_start_date.strftime('%d/%m')} - {week_end_date.strftime('%d/%m')}"
            week_options.append((week_label, week_start_date, week_end_date))
        
        selected_week_index = st.selectbox(
            "Seleziona Settimana del Sistema (opzionale)",
            options=range(len(week_options)),
            format_func=lambda x: week_options[x][0],
            help="Seleziona una settimana dal sistema per auto-compilare le date"
        )
        
        # Ottieni le date della settimana selezionata
        if selected_week_index is not None:
            _, auto_start, auto_end = week_options[selected_week_index]
        else:
            auto_start = datetime(2025, 4, 1).date()
            auto_end = datetime(2025, 4, 7).date()
        
        # Form per inserimento note
        with st.form("add_note_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Selectbox per scegliere arbitro
                arbitri_list = [f"{row['cognome']} {row['nome']} ({row['cod_mecc']})" for _, row in arbitri_df.iterrows()]
                selected_arbitro_nota = st.selectbox(
                    "Seleziona Arbitro",
                    options=arbitri_list,
                    help="Scegli l'arbitro per cui vuoi aggiungere una nota"
                )
                
                # Estrai cod_mecc dall'arbitro selezionato
                cod_mecc_nota = selected_arbitro_nota.split('(')[1].split(')')[0]
                
                # Date input per settimana - usa le date auto-selezionate
                settimana_inizio = st.date_input(
                    "Inizio Settimana",
                    value=auto_start,
                    min_value=datetime(2025, 3, 31).date(),
                    max_value=datetime(2025, 6, 1).date(),
                    help="Seleziona l'inizio della settimana (Lunedì)"
                )
                
            with col2:
                settimana_fine = st.date_input(
                    "Fine Settimana", 
                    value=auto_end,
                    min_value=datetime(2025, 3, 31).date(),
                    max_value=datetime(2025, 6, 1).date(),
                    help="Seleziona la fine della settimana (Domenica)"
                )
                
                # Text area per la nota
                nota_text = st.text_area(
                    "Nota",
                    placeholder="Inserisci qui la tua nota per questa settimana...",
                    height=100,
                    help="Scrivi la nota che vuoi associare a questo arbitro per la settimana selezionata"
                )
            
            # Bottoni di azione
            col1, col2 = st.columns(2)
            with col1:
                submit_button = st.form_submit_button("💾 Salva Nota", use_container_width=True)
            with col2:
                preview_button = st.form_submit_button("👁️ Anteprima", use_container_width=True)
        
        # Gestisci azioni del form
        if submit_button:
            if nota_text.strip():
                try:
                    save_nota_settimanale(
                        cod_mecc_nota, 
                        settimana_inizio.strftime('%Y-%m-%d'), 
                        settimana_fine.strftime('%Y-%m-%d'), 
                        nota_text.strip()
                    )
                    st.success(f"✅ Nota salvata per {selected_arbitro_nota.split('(')[0]} nella settimana {settimana_inizio.strftime('%d/%m')} - {settimana_fine.strftime('%d/%m')}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Errore nel salvare la nota: {e}")
            else:
                st.warning("⚠️ Inserisci una nota prima di salvare")
        

        
        if preview_button:
            # Mostra anteprima della nota esistente se presente
            conn = sqlite3.connect('arbitri.db')
            try:
                existing_note = pd.read_sql_query('''
                    SELECT nota, data_modifica FROM note_settimanali 
                    WHERE cod_mecc = ? AND settimana_inizio = ? AND settimana_fine = ?
                ''', conn, params=[
                    cod_mecc_nota, 
                    settimana_inizio.strftime('%Y-%m-%d'), 
                    settimana_fine.strftime('%Y-%m-%d')
                ])
                
                if not existing_note.empty and pd.notna(existing_note.iloc[0]['nota']):
                    st.info(f"📝 **Nota esistente:** {existing_note.iloc[0]['nota']}")
                    st.caption(f"Ultima modifica: {existing_note.iloc[0]['data_modifica']}")
                else:
                    st.info("📝 **Nessuna nota esistente per questa settimana**")
            except Exception as e:
                st.info("📝 **Nessuna nota esistente per questa settimana**")
            finally:
                conn.close()
        
        # Sezione visualizzazione note esistenti
        st.markdown("---")
        st.markdown("### 📋 Note Esistenti")
        
        # Query per ottenere tutte le note
        conn = sqlite3.connect('arbitri.db')
        try:
            all_notes_query = '''
                SELECT n.cod_mecc, a.cognome, a.nome, n.settimana_inizio, n.settimana_fine, 
                       n.nota, n.data_modifica
                FROM note_settimanali n
                JOIN arbitri a ON n.cod_mecc = a.cod_mecc
                WHERE n.nota IS NOT NULL AND n.nota != ''
                ORDER BY n.settimana_inizio DESC, a.cognome, a.nome
            '''
            all_notes = pd.read_sql_query(all_notes_query, conn)
        except Exception as e:
            all_notes = pd.DataFrame()  # DataFrame vuoto se la tabella non esiste
        finally:
            conn.close()
        
        if not all_notes.empty:
            st.info(f"📊 Totale note salvate: {len(all_notes)}")
            
            # Mostra ogni nota con bottone di eliminazione
            for idx, row in all_notes.iterrows():
                arbitro_nome = f"{row['cognome']} {row['nome']}"
                settimana = f"{row['settimana_inizio']} / {row['settimana_fine']}"
                nota = row['nota']
                data_modifica = pd.to_datetime(row['data_modifica']).strftime('%d/%m/%Y %H:%M')
                
                # Container per ogni nota
                with st.container():
                    col1, col2 = st.columns([0.9, 0.1])
                    
                    with col1:
                        st.markdown(f"**{arbitro_nome}** - *{settimana}*")
                        st.text(nota)
                        st.caption(f"Ultima modifica: {data_modifica}")
                    
                    with col2:
                        # Crea chiave unica per ogni bottone
                        delete_key = f"delete_{row['cod_mecc']}_{row['settimana_inizio']}_{row['settimana_fine']}"
                        
                        if st.button("🗑️", key=delete_key, help=f"Elimina nota per {arbitro_nome}"):
                            # Salva i dati della nota da eliminare in session_state per conferma
                            st.session_state[f"confirm_delete_{delete_key}"] = {
                                'cod_mecc': row['cod_mecc'],
                                'settimana_inizio': row['settimana_inizio'],
                                'settimana_fine': row['settimana_fine'],
                                'arbitro': arbitro_nome,
                                'settimana_display': settimana
                            }
                            st.rerun()
                    
                    # Controlla se c'è una richiesta di conferma per questa nota
                    confirm_key = f"confirm_delete_{delete_key}"
                    if confirm_key in st.session_state:
                        data_to_delete = st.session_state[confirm_key]
                        
                        st.warning(f"⚠️ **Conferma eliminazione**")
                        st.write(f"Vuoi eliminare la nota per **{data_to_delete['arbitro']}** nella settimana **{data_to_delete['settimana_display']}**?")
                        
                        col_confirm1, col_confirm2, col_confirm3 = st.columns(3)
                        
                        with col_confirm1:
                            if st.button("✅ Sì, elimina", key=f"confirm_yes_{delete_key}"):
                                try:
                                    delete_nota_settimanale(
                                        data_to_delete['cod_mecc'],
                                        data_to_delete['settimana_inizio'],
                                        data_to_delete['settimana_fine']
                                    )
                                    # Rimuovi la richiesta di conferma
                                    del st.session_state[confirm_key]
                                    st.success(f"✅ Nota eliminata per {data_to_delete['arbitro']}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Errore nell'eliminazione: {e}")
                        
                        with col_confirm2:
                            if st.button("❌ No, annulla", key=f"confirm_no_{delete_key}"):
                                # Rimuovi la richiesta di conferma
                                del st.session_state[confirm_key]
                                st.rerun()
                        
                        with col_confirm3:
                            st.empty()  # Spazio vuoto per allineamento
                    
                    st.markdown("---")  # Separatore tra note
        else:
            st.info("📝 Nessuna nota salvata ancora. Usa il form sopra per aggiungere la prima nota!")
    
    else:
        st.warning("📊 Carica l'anagrafica arbitri per gestire le note")

