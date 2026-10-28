@echo off
setlocal
title YouTube AI Project - Runner
cd /d "%~dp0"

echo ==========================================
echo YouTube AI Project - Pipeline Runner
echo ==========================================
echo.

:: Check if dependencies are installed
echo Checking dependencies...
python -c "import ollama" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [WARN] Ollama Python package not detected. Install dependencies first.
    echo.
)

echo.
echo ==========================================
echo Available Operations
echo ==========================================
echo.
echo 1. Full Pipeline   - Fetch transcript, chunk, embed, search, RAG
echo 2. Search Only     - Hybrid semantic/keyword search
echo 3. RAG Only        - Question answering with LLM
echo 4. Install Deps    - Install Python dependencies
echo 5. Help            - Show this menu
echo.
if not "%1"=="" (
    set "choice=%1"
    goto dispatch
)
set /p choice="Select operation (1-5): "

:dispatch
echo.
echo ==========================================

if "%choice%"=="1" goto full_pipeline
if "%choice%"=="2" goto search_only
if "%choice%"=="3" goto rag_only
if "%choice%"=="4" goto install_deps
if "%choice%"=="5" goto help
if "%choice%"=="" goto help

echo [ERROR] Invalid choice. Please select 1-5.
timeout /t 2 /nobreak >nul
goto help

:full_pipeline
echo.
echo [1/5] Full Pipeline Selected
echo.
set /p video_id="Enter YouTube Video ID (or press Enter to skip): "
if "%video_id%"=="" (
    echo Skipping transcript fetch.
) else (
    echo Fetching transcript for %video_id%...
    python src\fetch_transcript.py "%video_id%"
)
echo.
echo [2/5] Chunking all transcripts...
python src\chunker.py transcripts
echo.
echo [3/5] Generating embeddings for every video index...
python src\embed_chunks.py
echo.
echo [4/5] Search and RAG question answering
set /p question="Enter a question (or press Enter to skip): "
if "%question%"=="" (
    echo No question entered. Skipping search and RAG.
    goto full_done
)
python src\search.py "%question%"
echo.
python src\rag.py "%question%"
:full_done
echo.
echo ==========================================
echo FULL PIPELINE COMPLETE
echo ==========================================
goto end

:search_only
echo.
echo [SEARCH ONLY] Enter your question:
set /p question=
echo.
python src\search.py "%question%"
goto end

:rag_only
echo.
echo [RAG ONLY] Enter your question:
set /p question=
echo.
python src\rag.py "%question%"
goto end

:install_deps
echo.
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
echo.
echo Installation complete.
goto end

:help
echo.
echo Usage: run.bat [1-5]
echo.
echo Operations:
echo   1) Full Pipeline  - Complete workflow: fetch -^> chunk -^> embed -^> search -^> RAG
echo   2) Search Only    - Hybrid search on existing embedded data
echo   3) RAG Only       - LLM-powered question answering from transcripts
echo   4) Install Deps   - Install Python dependencies
echo   5) Help           - Show this menu
echo.
echo Examples:
echo   run.bat 1           # Full pipeline, will prompt for video ID
echo   run.bat 2           # Search existing data, will prompt for question
echo   run.bat 3           # RAG answering, will prompt for question
echo.
goto end

:end
echo.
pause
