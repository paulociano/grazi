# PyInstaller one-file build for the Windows installer.
from pathlib import Path
ROOT = Path(SPECPATH)
datas = [
    (str(ROOT / 'assets'), 'assets'),
    (str(ROOT / 'dictation.ps1'), '.'),
    (str(ROOT / 'wake_word.ps1'), '.'),
]
binaries = []
hiddenimports = ['edge_tts', 'send2trash']

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
