# Mastrino TEST - Sistema di Gestione Arbitri

Un'applicazione web Streamlit completa per la gestione degli arbitri di calcio della Serie A italiana. Il sistema gestisce dati anagrafici degli arbitri, assegnazioni delle partite, valutazioni delle prestazioni e tracciamento della disponibilità organizzato per settimane calcistiche dal 1-31 maggio 2025.

## 🚀 Caratteristiche Principali

- **Dashboard Settimanale**: Visualizzazione tabellare con settimane come colonne e arbitri come righe
- **Gestione Completa Dati**: Elaborazione file Excel/PDF con informazioni arbitri, partite e voti
- **Statistiche Avanzate**: Analisi prestazioni per categoria/girone e statistiche organi tecnici
- **Filtri Intelligenti**: Selezione arbitri specifici e periodi personalizzati
- **Export Excel**: Esportazione completa con fogli multipli e riepiloghi settimanali
- **Gestione Regioni**: Sistema partenze con regioni italiane per appartenenza/partenza
- **Indisponibilità**: Tracciamento periodi consecutivi di indisponibilità

## 📋 Funzionalità

### Dashboard Settimanale
- Visualizzazione gare per settimana (formato Lunedì-Domenica)
- Display formato "categoria + girone" (es. "CND A - ECC B")
- Informazioni dettagliate per partite multiple nella stessa settimana
- Filtri per arbitro specifico e periodi personalizzati

### Statistiche Generali
- Conteggio totale arbitri, partite e voti
- Statistiche indisponibilità con raggruppamento periodi consecutivi
- Visualizzazione arbitri più attivi (formato testo)
- Copertura percentuale voti OA/OT

### Statistiche Arbitraggio
- Analisi frequenza arbitraggio per categoria/girone
- Considerazione solo ruolo "AR" (Arbitro) dalla colonna 17

### Organi Tecnici
- Statistiche partite per organo tecnico per cognome
- Filtraggio solo gare con ruolo "OT" specifico
- Visualizzazione formato "COGNOME X GARE"

### Gestione Partenze
- Form per associare regioni italiane agli arbitri
- Filtri multipli: regione appartenenza, partenza, sezione
- Menu a tendina con tutte le 20 regioni d'Italia

## 🛠 Tecnologie

- **Frontend**: Streamlit
- **Backend**: Python, Pandas, SQLite
- **Database**: SQLite per persistenza dati locale
- **Elaborazione File**: PDFplumber per PDF, Pandas per Excel
- **Identificatore Unico**: Cod.Mecc per tutti i dati

## 📁 Struttura File

- `app.py` - Applicazione Streamlit principale
- `database.py` - Funzioni gestione database SQLite
- `file_processors.py` - Elaboratori file Excel/PDF
- `count_periods.py` - Logica raggruppamento periodi indisponibilità
- `data_loader.py` - Caricamento dati anagrafica
- `utils.py` - Funzioni utilità date e formattazione
- `export_utils.py` - Funzionalità export Excel
- `arbitri_anagrafica.xlsx` - File anagrafica arbitri incorporato

## 🚀 Installazione

1. Clona il repository
2. Installa le dipendenze:
   ```bash
   pip install streamlit pandas openpyxl pdfplumber
   ```
3. Esegui l'applicazione:
   ```bash
   streamlit run app.py --server.port 5000
   ```

## 📊 Schema Database

### Tabella `arbitri`
- Anagrafica completa con età, anzianità, sezione
- Regioni appartenenza e partenza
- Identificatore cod_mecc univoco

### Tabella `gare`
- Assegnazioni partite con categoria, girone, ruoli
- Collegamento arbitri tramite cod_mecc

### Tabella `voti`
- Valutazioni prestazioni con voti OA/OT
- Pattern "OT:X.X (COGNOME)" per organi tecnici

### Tabella `indisponibilita`
- Tracciamento disponibilità con raggruppamento periodi
- Filtri per qualifica specifica

## 📅 Organizzazione Temporale

Il sistema organizza i dati per settimane calcistiche:
- Formato Lunedì-Domenica
- Periodo: 1-31 Maggio 2025
- Visualizzazione tabellare efficiente

## 🔧 Configurazione

Il sistema si auto-configura al primo avvio caricando automaticamente l'anagrafica incorporata. Non sono richiesti upload manuali di file.

## 📈 Export e Reporting

- Export Excel completo con 5 fogli di lavoro
- Riepiloghi settimanali e statistiche dettagliate
- Dati età e anzianità inclusi in tutti i report

## 🤝 Contributi

Progetto sviluppato per la gestione arbitri Serie A italiana con focus su usabilità e completezza dati.