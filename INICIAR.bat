@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto dependencies
py -3 --version >nul 2>&1
if errorlevel 1 goto missing
py -3 -m venv .venv
if errorlevel 1 goto failed
:dependencies
".venv\Scripts\python.exe" -c "import PySide6" >nul 2>&1
if not errorlevel 1 goto launch
echo Preparando a Grazi. A primeira abertura requer internet...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
:launch
".venv\Scripts\python.exe" grazi.py
if errorlevel 1 goto failed
exit /b 0
:missing
echo Instale Python 3.12 de https://www.python.org/downloads/windows/
echo Inclua o Python Launcher durante a instalacao. Depois abra este arquivo novamente.
pause
exit /b 1
:failed
echo Nao foi possivel iniciar a Grazi. Copie o erro acima para diagnostico.
pause
exit /b 1
