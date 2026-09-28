@echo off
setlocal
cd /d "%~dp0"
set "GRAZI_ENV=.venv-py312"
py -3.12 -c "import sys,struct; sys.exit(0 if sys.version_info[:2] == (3,12) and struct.calcsize('P') == 8 else 1)" >nul 2>&1
if errorlevel 1 goto missing
if exist "%GRAZI_ENV%\Scripts\python.exe" goto validate
echo Criando ambiente Python 3.12 de 64 bits...
py -3.12 -m venv "%GRAZI_ENV%"
if errorlevel 1 goto failed
:validate
"%GRAZI_ENV%\Scripts\python.exe" -c "import sys,struct; sys.exit(0 if sys.version_info[:2] == (3,12) and struct.calcsize('P') == 8 else 1)" >nul 2>&1
if errorlevel 1 goto invalid
"%GRAZI_ENV%\Scripts\python.exe" -c "import PySide6, PySide6.QtWidgets, PySide6.QtTextToSpeech, PySide6.QtMultimedia, edge_tts; assert PySide6.__version__ == '6.8.3'" >nul 2>&1
if not errorlevel 1 goto launch
echo Preparando a Grazi com Python 3.12. A primeira abertura requer internet...
"%GRAZI_ENV%\Scripts\python.exe" -m pip install --retries 5 --timeout 60 -r requirements.txt
if errorlevel 1 goto failed
:launch
"%GRAZI_ENV%\Scripts\python.exe" grazi.py
if errorlevel 1 goto failed
exit /b 0
:missing
echo A Grazi precisa do Python 3.12 de 64 bits com Python Launcher.
echo Instale em https://www.python.org/downloads/release/python-31210/
echo Escolha Windows installer (64-bit). Mantenha o Python Launcher selecionado.
echo Voce pode manter outras versoes do Python instaladas.
echo Depois abra INICIAR.bat novamente.
pause
exit /b 1
:invalid
echo O ambiente .venv-py312 esta incompativel ou danificado.
echo Feche a Grazi, renomeie essa pasta e abra INICIAR.bat novamente.
pause
exit /b 1
:failed
echo Nao foi possivel iniciar a Grazi. Copie o erro acima para diagnostico.
echo Se aparecer ConnectionResetError 10054, verifique sua conexao e tente novamente.
pause
exit /b 1

