"""
Modulo per l'export HTML della Dashboard Arbitri (versione semplificata senza dipendenze PDF)
"""
import pandas as pd
import sqlite3
from datetime import datetime
import base64
import os

def create_arbitri_dashboard_html(selected_arbitro=None, start_date=None, end_date=None, logo_path=None):
    """
    Crea un file HTML della Dashboard Arbitri (versione semplificata)
    """
    try:
        # Genera nome file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if selected_arbitro and selected_arbitro != "Tutti":
            arbitro_name = selected_arbitro.replace(" ", "_").replace("(", "").replace(")", "")
            filename = f"Dashboard_Arbitri_{arbitro_name}_{timestamp}.html"
        else:
            filename = f"Dashboard_Arbitri_Completa_{timestamp}.html"
        
        # Inizio HTML
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Dashboard Arbitri - Mastrino TEST</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { text-align: center; color: #1f4e79; margin-bottom: 30px; }
                .logo { text-align: center; margin-bottom: 20px; }
                .stats { background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
                th { background-color: #1f4e79; color: white; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .footer { text-align: center; margin-top: 40px; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
        """
        
        # Logo AIA (se presente)
        if logo_path and os.path.exists(logo_path):
            try:
                with open(logo_path, "rb") as img_file:
                    img_b64 = base64.b64encode(img_file.read()).decode()
                    img_ext = logo_path.split('.')[-1].lower()
                    html_content += f'<div class="logo"><img src="data:image/{img_ext};base64,{img_b64}" width="200"></div>'
            except:
                pass
        
        # Titolo
        title_text = "CAN D"
        subtitle_text = "DASHBOARD ARBITRI"
        if selected_arbitro and selected_arbitro != "Tutti":
            subtitle_text += f" - Arbitro: {selected_arbitro}"
            
        html_content += f'<div class="header"><h1 style="font-weight: 900; color: white; font-family: Arial, sans-serif; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);"><strong>{title_text}</strong></h1><h2>{subtitle_text}</h2></div>'
        
        # Periodo
        period_text = f"Periodo: {start_date.strftime('%d/%m/%Y') if start_date else 'Inizio'} - {end_date.strftime('%d/%m/%Y') if end_date else 'Fine'}"
        html_content += f'<p style="text-align: center;"><strong>{period_text}</strong></p>'
        
        # Ottieni dati dal database
        conn = sqlite3.connect('arbitri.db')
        
        # Query per ottenere dati dashboard
        dashboard_query = """
            SELECT 
                a.cognome || ' ' || a.nome as arbitro,
                a.sezione,
                COALESCE(a.eta, '') as eta,
                COUNT(DISTINCT g.numero_gara) as totale_gare,
                COUNT(DISTINCT CASE WHEN v.voto_oa IS NOT NULL THEN g.numero_gara END) as gare_con_voto_oa,
                COUNT(DISTINCT CASE WHEN v.voto_ot IS NOT NULL THEN g.numero_gara END) as gare_con_voto_ot,
                GROUP_CONCAT(DISTINCT COALESCE(g.categoria, '') || ' ' || COALESCE(g.girone, '')) as categorie
            FROM arbitri a
            LEFT JOIN gare g ON a.cod_mecc = g.cod_mecc
            LEFT JOIN voti v ON g.numero_gara = v.numero_gara
            WHERE 1=1
        """
        
        params = []
        if selected_arbitro and selected_arbitro != "Tutti" and selected_arbitro != "Tutti gli arbitri":
            dashboard_query += " AND (a.cognome || ' ' || a.nome LIKE ? OR a.cod_mecc LIKE ?)"
            search_term = f"%{selected_arbitro}%"
            params.extend([search_term, search_term])
        
        if start_date:
            dashboard_query += " AND (g.data_gara IS NULL OR g.data_gara >= ?)" 
            params.append(start_date.strftime('%Y-%m-%d'))
            
        if end_date:
            dashboard_query += " AND (g.data_gara IS NULL OR g.data_gara <= ?)"
            params.append(end_date.strftime('%Y-%m-%d'))
        
        dashboard_query += """
            GROUP BY a.cod_mecc, a.cognome, a.nome, a.sezione, a.eta
            HAVING COUNT(DISTINCT g.numero_gara) > 0 OR ? = 'Tutti'
            ORDER BY totale_gare DESC, arbitro
        """
        params.append(selected_arbitro if selected_arbitro else 'Tutti')
        
        df = pd.read_sql_query(dashboard_query, conn, params=params)
        conn.close()
        
        if not df.empty:
            # Statistiche generali
            html_content += f'''
            <div class="stats">
                <h2>📊 STATISTICHE GENERALI</h2>
                <p><strong>Totale Arbitri:</strong> {len(df)}</p>
                <p><strong>Totale Gare:</strong> {df['totale_gare'].sum()}</p>
                <p><strong>Media Gare per Arbitro:</strong> {df['totale_gare'].mean():.1f}</p>
                <p><strong>Gare con Voti OA:</strong> {df['gare_con_voto_oa'].sum()}</p>
                <p><strong>Gare con Voti OT:</strong> {df['gare_con_voto_ot'].sum()}</p>
            </div>
            '''
            
            # Tabella arbitri
            html_content += '<h2>👥 DETTAGLIO ARBITRI</h2>'
            html_content += '<table>'
            html_content += '<tr><th>Arbitro</th><th>Sez.</th><th>Età</th><th>Gare</th><th>Voti OA</th><th>Voti OT</th><th>Categorie</th></tr>'
            
            for _, row in df.head(30).iterrows():
                html_content += f'''
                <tr>
                    <td>{str(row['arbitro'])[:30]}</td>
                    <td>{str(row['sezione']) if pd.notna(row['sezione']) else ''}</td>
                    <td>{str(int(row['eta'])) if pd.notna(row['eta']) else ''}</td>
                    <td>{str(int(row['totale_gare']))}</td>
                    <td>{str(int(row['gare_con_voto_oa']))}</td>
                    <td>{str(int(row['gare_con_voto_ot']))}</td>
                    <td>{str(row['categorie'])[:40] if pd.notna(row['categorie']) else ''}</td>
                </tr>
                '''
            
            html_content += '</table>'
        else:
            html_content += '<p>⚠️ Nessun dato disponibile per i filtri selezionati</p>'
        
        # Footer
        html_content += f'''
        <div class="footer">
            <p>Generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')} - Sistema Mastrino TEST</p>
        </div>
        </body>
        </html>
        '''
        
        # Salva file HTML
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return {
            'success': True,
            'message': f'Dashboard HTML generata: {filename}',
            'filename': filename
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Errore nella generazione PDF: {str(e)}'
        }

def get_html_download_link(filename):
    """
    Genera link per download HTML in Streamlit
    """
    try:
        with open(filename, "r", encoding='utf-8') as html_file:
            html_content = html_file.read()
            b64 = base64.b64encode(html_content.encode('utf-8')).decode()
            return f'<a href="data:text/html;base64,{b64}" download="{filename}">📄 Scarica Dashboard HTML</a>'
    except Exception as e:
        return f"Errore nel creare link download: {e}"