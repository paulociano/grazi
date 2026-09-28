# PyInstaller one-directory build for the Windows installer.
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH)
datas = [
    (str(ROOT / 'assets'), 'assets'),
    (str(ROOT / 'dictation.ps1'), '.'),
    (str(ROOT / 'wake_word.ps1'), '.'),
]
binaries = []
hiddenimports = ['edge_tts', 'send2trash']
for package in ('PySide6', 'edge_tts', 'send2trash'):
    try:
        package_datas, package_binaries, package_hidden = collect_all(package)
        datas += package_datas
        binaries += package_binaries
        hiddenimports += package_hidden
    except Exception:
        pass

a = Analysis(
    ['grazi.py'],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'pytest', 'tests'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Grazi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(ROOT / 'assets' / 'grazi.ico') if (ROOT / 'assets' / 'grazi.ico').exists() else None,
)
