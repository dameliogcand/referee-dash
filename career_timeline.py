"""
Interactive Referee Career Timeline Module
Provides detailed career progression analysis for individual referees
"""

import pandas as pd
import sqlite3
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from plotly.subplots import make_subplots

def get_referee_career_data(cod_mecc):
    """Get comprehensive career data for a specific referee"""
    conn = sqlite3.connect('arbitri.db')
    
    # Basic referee info
    referee_query = """
        SELECT a.cod_mecc, a.cognome, a.nome, a.sezione, a.eta, a.anno_anzianita
        FROM arbitri a
        WHERE a.cod_mecc = ?
    """
    referee_info = pd.read_sql_query(referee_query, conn, params=[cod_mecc])
    
    # Career games with detailed info
    games_query = """
        SELECT g.numero_gara, g.data_gara, g.categoria, g.girone, g.ruolo,
               g.squadra_casa, g.squadra_trasferta, g.campionato,
               v.voto_oa, v.voto_ot
        FROM gare g
        LEFT JOIN voti v ON g.numero_gara = v.numero_gara
        WHERE g.cod_mecc = ?
        ORDER BY g.data_gara ASC
    """
    games_data = pd.read_sql_query(games_query, conn, params=[cod_mecc])
    
    # Unavailability periods
    unavail_query = """
        SELECT data_indisponibilita, motivo
        FROM indisponibilita
        WHERE cod_mecc = ?
        ORDER BY data_indisponibilita ASC
    """
    unavail_data = pd.read_sql_query(unavail_query, conn, params=[cod_mecc])
    
    conn.close()
    
    return referee_info, games_data, unavail_data

def create_career_timeline_chart(games_data, unavail_data):
    """Create interactive timeline chart showing career progression"""
    if games_data.empty:
        return None
    
    # Convert dates
    games_data['data_gara'] = pd.to_datetime(games_data['data_gara'])
    
    # Create timeline with games and ratings
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Games Timeline', 'Performance Ratings', 'Category Distribution'),
        vertical_spacing=0.08,
        row_heights=[0.4, 0.3, 0.3]
    )
    
    # Games timeline (scatter plot)
    colors = {'AR': '#1f4e79', 'AA1': '#2e8b57', 'AA2': '#ff6b35', 'OA': '#8b0000'}
    
    for ruolo in games_data['ruolo'].unique():
        if pd.notna(ruolo):
            subset = games_data[games_data['ruolo'] == ruolo]
            fig.add_trace(
                go.Scatter(
                    x=subset['data_gara'],
                    y=[ruolo] * len(subset),
                    mode='markers',
                    name=ruolo,
                    marker=dict(
                        color=colors.get(ruolo, '#666666'),
                        size=8,
                        symbol='circle'
                    ),
                    hovertemplate='<b>%{y}</b><br>' +
                                'Data: %{x}<br>' +
                                '<extra></extra>',
                    showlegend=True
                ),
                row=1, col=1
            )
    
    # Performance ratings over time
    rated_games = games_data.dropna(subset=['voto_oa'])
    if not rated_games.empty:
        fig.add_trace(
            go.Scatter(
                x=rated_games['data_gara'],
                y=rated_games['voto_oa'],
                mode='lines+markers',
                name='Voti OA',
                line=dict(color='#1f4e79', width=2),
                marker=dict(size=6),
                hovertemplate='<b>Voto OA: %{y}</b><br>' +
                            'Data: %{x}<br>' +
                            '<extra></extra>'
            ),
            row=2, col=1
        )
    
    rated_games_ot = games_data.dropna(subset=['voto_ot'])
    if not rated_games_ot.empty:
        fig.add_trace(
            go.Scatter(
                x=rated_games_ot['data_gara'],
                y=rated_games_ot['voto_ot'],
                mode='lines+markers',
                name='Voti OT',
                line=dict(color='#ff6b35', width=2),
                marker=dict(size=6),
                hovertemplate='<b>Voto OT: %{y}</b><br>' +
                            'Data: %{x}<br>' +
                            '<extra></extra>'
            ),
            row=2, col=1
        )
    
    # Category progression
    cat_counts = games_data.groupby(['data_gara', 'categoria']).size().reset_index(name='count')
    if not cat_counts.empty:
        categories = cat_counts['categoria'].unique()
        for cat in categories:
            if pd.notna(cat):
                cat_subset = cat_counts[cat_counts['categoria'] == cat]
                fig.add_trace(
                    go.Scatter(
                        x=cat_subset['data_gara'],
                        y=[cat] * len(cat_subset),
                        mode='markers',
                        name=f'Cat. {cat}',
                        marker=dict(size=cat_subset['count'] * 3, opacity=0.7),
                        showlegend=False,
                        hovertemplate='<b>%{y}</b><br>' +
                                    'Data: %{x}<br>' +
                                    'Gare: %{marker.size}<br>' +
                                    '<extra></extra>'
                    ),
                    row=3, col=1
                )
    
    # Add unavailability periods as vertical lines
    if not unavail_data.empty:
        unavail_data['data_indisponibilita'] = pd.to_datetime(unavail_data['data_indisponibilita'])
        for _, unavail in unavail_data.iterrows():
            fig.add_vline(
                x=unavail['data_indisponibilita'],
                line_dash="dash",
                line_color="red",
                annotation_text=f"Indisponibile: {unavail['motivo'][:20]}",
                annotation_position="top"
            )
    
    # Update layout
    fig.update_layout(
        height=800,
        title="Career Timeline",
        showlegend=True,
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Data", row=3, col=1)
    fig.update_yaxes(title_text="Ruolo", row=1, col=1)
    fig.update_yaxes(title_text="Voto", row=2, col=1, range=[5, 10])
    fig.update_yaxes(title_text="Categoria", row=3, col=1)
    
    return fig

def calculate_career_metrics(referee_info, games_data):
    """Calculate key career performance metrics"""
    if games_data.empty:
        return {}
    
    # Convert dates for calculations
    games_data['data_gara'] = pd.to_datetime(games_data['data_gara'])
    
    # Basic stats
    total_games = len(games_data)
    roles = games_data['ruolo'].value_counts().to_dict()
    categories = games_data['categoria'].value_counts().to_dict()
    
    # Performance metrics - exclude QU role from both OA and OT averages
    non_qu_games = games_data[games_data['ruolo'] != 'QU']
    avg_oa = non_qu_games['voto_oa'].mean() if not non_qu_games['voto_oa'].isna().all() else None
    avg_ot = non_qu_games['voto_ot'].mean() if not non_qu_games['voto_ot'].isna().all() else None
    
    # Career span
    first_game = games_data['data_gara'].min()
    last_game = games_data['data_gara'].max()
    
    # Recent performance (last 10 games) - exclude QU from both OA and OT
    recent_games = games_data.nlargest(10, 'data_gara')
    recent_non_qu = recent_games[recent_games['ruolo'] != 'QU']
    recent_avg_oa = recent_non_qu['voto_oa'].mean() if not recent_non_qu['voto_oa'].isna().all() else None
    recent_avg_ot = recent_non_qu['voto_ot'].mean() if not recent_non_qu['voto_ot'].isna().all() else None
    
    # Experience calculation
    if not referee_info.empty and pd.notna(referee_info.iloc[0]['anno_anzianita']):
        experience_years = 2025 - int(referee_info.iloc[0]['anno_anzianita'])
    else:
        experience_years = None
    
    return {
        'total_games': total_games,
        'roles': roles,
        'categories': categories,
        'avg_oa': avg_oa,
        'avg_ot': avg_ot,
        'first_game': first_game,
        'last_game': last_game,
        'recent_avg_oa': recent_avg_oa,
        'recent_avg_ot': recent_avg_ot,
        'experience_years': experience_years,
        'games_with_oa_rating': non_qu_games['voto_oa'].notna().sum(),
        'games_with_ot_rating': non_qu_games['voto_ot'].notna().sum(),
        'total_oa_ratings_with_qu': games_data['voto_oa'].notna().sum(),
        'total_ot_ratings_with_qu': games_data['voto_ot'].notna().sum()
    }

def display_career_summary(referee_info, metrics):
    """Display career summary cards"""
    if referee_info.empty:
        return
    
    referee = referee_info.iloc[0]
    
    # Header with referee info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Arbitro",
            f"{referee['cognome']} {referee['nome']}",
            delta=f"Sezione {referee['sezione']}" if pd.notna(referee['sezione']) else None
        )
    
    with col2:
        if metrics.get('experience_years'):
            st.metric(
                "Esperienza",
                f"{metrics['experience_years']} anni",
                delta=f"Età: {referee['eta']}" if pd.notna(referee['eta']) else None
            )
    
    with col3:
        st.metric(
            "Totale Gare",
            metrics['total_games'],
            delta=f"Con voti: {metrics['games_with_oa_rating']}"
        )
    
    # Performance metrics
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if metrics.get('avg_oa'):
            delta_text = f"Valutazioni: {metrics['games_with_oa_rating']}"
            if metrics.get('total_oa_ratings_with_qu', 0) > metrics.get('games_with_oa_rating', 0):
                excluded_qu_oa = metrics['total_oa_ratings_with_qu'] - metrics['games_with_oa_rating']
                delta_text += f" (esclusi {excluded_qu_oa} QU)"
            
            recent_delta = None
            if metrics.get('recent_avg_oa'):
                recent_delta = f"Recenti: {metrics['recent_avg_oa']:.2f}"
            
            st.metric(
                "Media Voti OA",
                f"{metrics['avg_oa']:.2f}",
                delta=recent_delta if recent_delta else delta_text
            )
            
            if recent_delta and delta_text:
                st.caption(delta_text)
    
    with col5:
        if metrics.get('avg_ot'):
            delta_text = f"Valutazioni: {metrics['games_with_ot_rating']}"
            if metrics.get('total_ot_ratings_with_qu', 0) > metrics.get('games_with_ot_rating', 0):
                excluded_qu = metrics['total_ot_ratings_with_qu'] - metrics['games_with_ot_rating']
                delta_text += f" (esclusi {excluded_qu} QU)"
            
            recent_delta = None
            if metrics.get('recent_avg_ot'):
                recent_delta = f"Recenti: {metrics['recent_avg_ot']:.2f}"
            
            st.metric(
                "Media Voti OT",
                f"{metrics['avg_ot']:.2f}",
                delta=recent_delta if recent_delta else delta_text
            )
            
            if recent_delta and delta_text:
                st.caption(delta_text)
    
    with col6:
        if metrics.get('first_game') and metrics.get('last_game'):
            career_span = (metrics['last_game'] - metrics['first_game']).days
            st.metric(
                "Carriera Attiva",
                f"{career_span} giorni",
                delta=f"Dal {metrics['first_game'].strftime('%d/%m/%Y')}"
            )

def show_detailed_games_table(games_data):
    """Show detailed games history table"""
    if games_data.empty:
        st.warning("Nessuna gara trovata per questo arbitro")
        return
    
    # Prepare display data
    display_data = games_data.copy()
    display_data['data_gara'] = pd.to_datetime(display_data['data_gara']).dt.strftime('%d/%m/%Y')
    
    # Select and rename columns for display
    columns_to_show = {
        'data_gara': 'Data',
        'categoria': 'Categoria',
        'girone': 'Girone',
        'ruolo': 'Ruolo',
        'squadra_casa': 'Casa',
        'squadra_trasferta': 'Trasferta',
        'voto_oa': 'Voto OA',
        'voto_ot': 'Voto OT'
    }
    
    display_data = display_data[list(columns_to_show.keys())].rename(columns=columns_to_show)
    
    # Format ratings
    for col in ['Voto OA', 'Voto OT']:
        display_data[col] = display_data[col].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "-"
        )
    
    # Display with sorting and filtering
    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Data": st.column_config.TextColumn("Data", width="small"),
            "Categoria": st.column_config.TextColumn("Categoria", width="small"),
            "Girone": st.column_config.TextColumn("Girone", width="small"),
            "Ruolo": st.column_config.TextColumn("Ruolo", width="small"),
            "Casa": st.column_config.TextColumn("Casa", width="medium"),
            "Trasferta": st.column_config.TextColumn("Trasferta", width="medium"),
            "Voto OA": st.column_config.TextColumn("Voto OA", width="small"),
            "Voto OT": st.column_config.TextColumn("Voto OT", width="small")
        }
    )

def create_performance_trends_chart(games_data):
    """Create performance trends analysis"""
    if games_data.empty or games_data['voto_oa'].isna().all():
        return None
    
    # Prepare data
    games_with_ratings = games_data.dropna(subset=['voto_oa']).copy()
    games_with_ratings['data_gara'] = pd.to_datetime(games_with_ratings['data_gara'])
    games_with_ratings = games_with_ratings.sort_values('data_gara')
    
    # Calculate rolling averages
    games_with_ratings['rolling_avg_3'] = games_with_ratings['voto_oa'].rolling(window=3, min_periods=1).mean()
    games_with_ratings['rolling_avg_5'] = games_with_ratings['voto_oa'].rolling(window=5, min_periods=1).mean()
    
    # Create chart
    fig = go.Figure()
    
    # Individual ratings
    fig.add_trace(go.Scatter(
        x=games_with_ratings['data_gara'],
        y=games_with_ratings['voto_oa'],
        mode='markers',
        name='Voti Individuali',
        marker=dict(color='lightblue', size=6, opacity=0.6),
        hovertemplate='<b>Voto: %{y}</b><br>Data: %{x}<br><extra></extra>'
    ))
    
    # Rolling averages
    fig.add_trace(go.Scatter(
        x=games_with_ratings['data_gara'],
        y=games_with_ratings['rolling_avg_3'],
        mode='lines',
        name='Media Mobile (3)',
        line=dict(color='#1f4e79', width=2),
        hovertemplate='<b>Media 3: %{y:.2f}</b><br>Data: %{x}<br><extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=games_with_ratings['data_gara'],
        y=games_with_ratings['rolling_avg_5'],
        mode='lines',
        name='Media Mobile (5)',
        line=dict(color='#ff6b35', width=2),
        hovertemplate='<b>Media 5: %{y:.2f}</b><br>Data: %{x}<br><extra></extra>'
    ))
    
    # Add reference lines
    overall_avg = games_with_ratings['voto_oa'].mean()
    fig.add_hline(y=overall_avg, line_dash="dash", line_color="green", 
                  annotation_text=f"Media Generale: {overall_avg:.2f}")
    
    fig.update_layout(
        title="Andamento Performance nel Tempo",
        xaxis_title="Data",
        yaxis_title="Voto OA",
        yaxis=dict(range=[5, 10]),
        height=400,
        hovermode='x unified'
    )
    
    return fig