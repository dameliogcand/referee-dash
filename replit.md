# Overview

This is "Mastrino TEST" - a complete Streamlit-based web application for managing Italian Serie A football referees (arbitri). The system handles referee registry data, match assignments, performance ratings, and availability tracking organized by weekly football schedules from May 1-31, 2025. It provides a user-friendly interface for uploading and processing Excel/PDF files containing referee information, match data, and performance evaluations with incremental data updates (no overwriting).

# User Preferences

Preferred communication style: Simple, everyday language.
Date: August 2, 2025 - User requested Italian football referee management system with weekly calendar organization for May 2025.

## Recent Updates (August 3, 2025)
- Renamed system to "Mastrino TEST"
- Implemented OT (Organo Tecnico) cognome display: voti OT now show "OT:7.5 (COGNOME)"
- Added referee filter: users can select specific arbiters or view all
- Implemented complete database auto-population with anzianità OT from graduatoria PDF
- Added separate "Età" and "Anzianità" columns for all referee data
- Extracted età and anzianità from Excel file updating 207 arbiters with accurate data
- Created comprehensive Excel export with 5 sheets including age and seniority data
- Implemented date filtering system for custom period selection
- Optimized table display: removed index numbers and cod_mecc column
- Optimized column widths - Sez. (45px), Età (45px), Anz. (45px)
- Statistics now consider only AR (Arbitro) role games from CRA01 column 17
- Indisponibilità statistics fixed to show 114 AR periods as required
- Enhanced multiple games per week visualization with detailed info
- Added new "Organi Tecnici" tab showing games per technical officer by surname
- Removed "Dati Completi" tab for cleaner interface
- Enhanced statistics with OA/OT vote counts and coverage percentage
- Changed "Arbitri Più Attivi" from chart to text list showing game counts
- Added "Partenze" tab for managing referee regions (appartenenza/partenza) with filtering capabilities
- Extended arbitri table with regione_appartenenza and regione_partenza columns
- Corrected week ranges to proper Monday-Sunday calendar format
- Fixed column auto-sizing and row height adaptation
- Updated legend: OT = "Organo Tecnico" (not "Osservatore Tecnico")
- Embedded Excel anagrafica file in project (no upload required)
- Changed display from game numbers to category + girone format (e.g., "CND A - ECC B")
- Implemented tabular interface: weeks as columns, referees as rows
- Added comprehensive Excel export functionality with multiple sheets
- Created referee statistics page showing arbitration frequency by category/girone
- Resolved referee duplication issue (anagrafica was loaded twice with different code formats)
- Created complete database population script eliminating need for manual file uploads
- **August 3**: Fixed Streamlit Cloud deployment - resolved ImportError and database auto-population
- **August 3**: Removed bar chart from Organi Tecnici tab for cleaner interface
- **August 3**: Added "Voti OT Ricevuti per Arbitro" table showing vote count statistics
- **August 3**: Implemented HTML dashboard export with AIA logo integration and professional styling
- **August 3**: Added automatic filter session management for export functionality
- **August 3**: Finalized AIA branding with centered logo and "CAN D" in white FIGC bold font
- **August 3**: Completed HTML dashboard export functionality with SQL optimization and unified button styling
- **August 3**: Final system testing confirmed - all features working correctly including exports and branding
- **August 3**: Added Interactive Referee Career Timeline with comprehensive career analysis, performance trends, and detailed match history
- **August 3**: Enhanced Career Timeline to exclude QU (Quarto Uomo) role from both OA and OT vote averages as requested
- **August 3**: Updated main Dashboard to exclude QU roles from all displays, calculations, and statistics including weekly view and general statistics
- **August 3**: Enhanced "Voti OT Ricevuti per Arbitro" table to show Cognome, Nome, Sezione and exclude QU from vote counts
- **August 3**: User confirmed all QU exclusion functionality working correctly system-wide
- **August 3**: Implemented complete weekly note management system with database storage, interactive interface, and dashboard integration
- **August 3**: Added new "Gestione Note" tab with full CRUD operations for personalized weekly referee notes
- **August 3**: Fixed note display issue in weekly dashboard - notes now correctly appear with 📝 icon using flexible date matching
- **August 3**: Enhanced note management with automatic week selection from system calendar for accurate date alignment
- **August 3**: User confirmed complete note management system working perfectly
- **August 3**: Reorganized tab order per user request: Dashboard→Statistiche Arbitraggio→Organi Tecnici→Statistiche Generali→Timeline Carriera→Partenze→Gestione Note
- **August 3**: Reverted tab order to previous version: Dashboard→Statistiche Generali→Statistiche Arbitraggio→Organi Tecnici→Timeline Carriera→Partenze→Gestione Note
- **August 3**: Inverted Timeline and Partenze tabs: Dashboard→Statistiche Generali→Statistiche Arbitraggio→Organi Tecnici→Partenze→Timeline Carriera→Gestione Note
- **August 3**: Final system organization completed and confirmed working correctly
- **August 3**: Created complete deployment package (mastrino-deploy-package.tar.gz) with all files, documentation, and requirements
- **August 3**: Added robust pdfplumber fallback handling for deployment compatibility
- **August 3**: Generated comprehensive deployment guides and package documentation
- **August 3**: Updated deployment package to include pre-populated database (arbitri.db) for immediate startup
- **August 3**: Final package size: 154KB with complete working system ready for production deployment
- **August 3**: Created complete GitHub package (mastrino-github-complete.tar.gz) with all files, database, and comprehensive documentation for immediate repository upload and deployment
- **August 3**: Fixed critical note management bug - tabella note_settimanali mancante causava errori in delete/modify operations, implementato auto-creazione tabella e interface migliorata per caricamento note esistenti
- **August 3**: Fixed Streamlit form error - moved note loading button outside st.form() per compliance con Streamlit API, aggiunta sezione dedicata per caricamento note esistenti
- **August 3**: Enhanced note deletion system - added individual trash button (🗑️) next to each note with confirmation dialog for safer note management, removed bulk delete from form
- **August 3**: Removed "Carica Nota Esistente" section per user request
- **August 3**: Added fixed left column for "Arbitro" in Dashboard table to improve horizontal scrolling navigation
- **August 3**: Redesigned header with modern gradient background, professional typography, and glass-morphism effects replacing old logo/CAN D design
- **August 3**: Integrated AIA logo into modern header with appropriate 60px sizing and base64 embedding for reliable display
- **August 3**: Changed main title from "MASTRINO" to "REFEREE DASHBOARD" per user request
- **August 3**: Updated subtitle from "GESTIONE ARBITRI" to "CAN D" for official branding alignment
- **August 3**: Enhanced "CAN D" visibility with larger font size (1.8rem), bold weight (800), and stronger shadow effects
- **August 3**: Further increased "CAN D" size to 2.5rem with Arial Black font, weight 900, and enhanced shadow for maximum visibility
- **August 3**: Unified font family for "CAN D" to match "REFEREE DASHBOARD" using Segoe UI, adjusted size to 2.4rem for consistency
- **August 3**: Updated header description from "Sistema professionale per..." to "Sistema per la gestione e monitoraggio degli arbitri di calcio"
- **August 3**: Repositioned "CAN D" vertically on the right side of header using CSS writing-mode and absolute positioning
- **August 3**: Fixed "CAN D" vertical display using transform rotate(-90deg) and white-space nowrap for better browser compatibility
- **August 3**: Redesigned "CAN D" vertical display using flex-direction column with individual letters for guaranteed visibility
- **August 3**: Final header redesign with professional gradient background, "CAN D" as subtle watermark (opacity 0.12) in background, enhanced logo presentation with premium styling, and smooth gradient animation
- **August 4**: Implemented clean professional header with Logo AIA, "REFEREE DASHBOARD" title, and "CAN D" watermark using optimized HTML/CSS for reliable Streamlit rendering
- **August 4**: Updated header subtitle to "Sistema per la gestione e il monitoraggio degli arbitri di calcio" and enlarged AIA logo to 80px for better visibility
- **August 4**: VERSIONE FINALE confermata - Sistema completo con testata professionale, tutte le funzionalità operative, database pre-popolato, export Excel/HTML, gestione note settimanali, timeline carriera interattiva
- **August 4**: Implementato periodo di test aprile 2025 - Sistema esteso per supportare caricamento dati 01/04/25 - 30/04/25, aggiornate funzioni get_week_ranges() e filtri dashboard, database preparato con indici performance

# System Architecture

## Frontend Architecture
- **Framework**: Streamlit web application framework
- **Layout**: Wide layout with expandable sidebar for file uploads and export
- **User Interface**: Four-tab dashboard with tabular weekly view, statistics, and data management
- **Page Configuration**: Custom page title, icon (⚽), and sidebar state management
- **Export Feature**: Excel download with multiple sheets and weekly summaries

## Backend Architecture
- **Database**: SQLite database for local data persistence
- **File Processing**: Modular file processors for different data types (Excel, PDF)
- **Data Models**: Four main entities - arbitri (referees), gare (matches), voti (ratings), and indisponibilita (availability)
- **Database Schema**:
  - `arbitri` table: referee registry with mechanical code, name, section, age (auto-loaded from embedded Excel)
  - `gare` table: match assignments with categoria, girone, referee assignments and match details
  - `voti` table: performance ratings linked to matches
  - `indisponibilita` table: referee availability tracking with date ranges and motivo
- **Auto-loading**: Embedded anagrafica Excel file loaded automatically on startup

## Data Processing Pipeline
- **Excel Processing**: Pandas-based processing for referee registry and match data
- **PDF Processing**: PDFplumber for extracting performance ratings from PDF documents
- **Column Mapping**: Flexible column name mapping to handle variations in input file formats
- **Data Validation**: Input validation and error handling with user feedback

## Utility Functions
- **Week Management**: Date utility functions for organizing data by weekly periods
- **Date Formatting**: Standardized date display formatting across the application

# External Dependencies

## Core Libraries
- **Streamlit**: Web application framework for the user interface
- **Pandas**: Data manipulation and Excel file processing
- **SQLite3**: Built-in database for data persistence
- **PDFplumber**: PDF text extraction for processing rating documents

## Database
- **SQLite**: Local file-based database (`arbitri.db`) for storing all application data
- **Schema**: Relational design with foreign key constraints between tables

## File Format Support
- **Excel Files**: .xlsx and .xls formats for referee and match data
- **PDF Files**: PDF format support for performance rating documents
- **Data Sources**: Supports CRA01 format for match assignments and various referee data formats