@echo off
setlocal
cd /d "%~dp0"
set "VENV=.venv-build"
if not exist "%VENV%\Scripts\python.exe" py -3.12 -m venv "%VENV%"
if errorlevel 1 goto failed
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip
"%VENV%\Scripts\python.exe" -m pip install -r requirements.txt -r requirements-build.txt
if errorlevel 1 goto failed
"%VENV%\Scripts\python.exe" -m PyInstaller --noconfirm --clean grazi.spec
if errorlevel 1 goto failed
where ISCC.exe >nul 2>&1
if errorlevel 1 (
  echo Instale o Inno Setup 6 para gerar o instalador final: https://jrsoftware.org/isinfo.php
  pause
  exit /b 1
)
ISCC.exe installer.iss
if errorlevel 1 goto failed
echo Instalador criado em installer-output\Grazi-Setup-v0.9.0.exe
pause
exit /b 0
:failed
echo Falha ao criar o instalador. Copie a mensagem acima para diagnostico.
pause
exit /b 1
