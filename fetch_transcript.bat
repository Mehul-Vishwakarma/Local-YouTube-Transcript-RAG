@echo off
setlocal

echo ==========================================
echo   YouTube Transcript Fetcher
echo ==========================================
echo.

set /p VIDEO_ID=Enter YouTube video ID (the part after v= in the URL): 

if "%VIDEO_ID%"=="" (
    echo No video ID entered. Exiting.
    pause
    exit /b 1
)

echo.
python fetch_transcript.py "%VIDEO_ID%"

echo.
pause