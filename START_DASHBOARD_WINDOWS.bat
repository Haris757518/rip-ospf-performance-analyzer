@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% neq 0 (
  echo Python launcher not found. Install Python 3.10+ and select Add Python to PATH.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  py -m venv .venv
  if errorlevel 1 goto error
)
".venv\Scripts\python.exe" -c "import streamlit, pandas, plotly" >nul 2>nul
if not errorlevel 1 goto launch
echo Installing Streamlit and dashboard dependencies (internet required first time)...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if %errorlevel% neq 0 goto error
:launch
".venv\Scripts\python.exe" -m streamlit run dashboard\app.py
exit /b %errorlevel%
:error
echo Setup failed. Review the message above and try again while online.
pause
exit /b 1
