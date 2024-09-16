# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('/Users/bardamri/PycharmProjects/SportScrapper/assets/config.json', 'assets/config.json'),
        ('/Users/bardamri/PycharmProjects/SportScrapper/assets/translations.json', 'assets/translations.json'),
        ('/Users/bardamri/PycharmProjects/SportScrapper/assets/entrancePageImage.png', 'assets/entrancePageImage.png'),
        ('/Users/bardamri/PycharmProjects/SportScrapper/assets/icon.png', 'assets/icon.png'),
        ('/Users/bardamri/PycharmProjects/SportScrapper/assets/icon.ico', 'assets/icon.ico'),
        ('/Users/bardamri/PycharmProjects/SportScrapper/assets/requirements.txt', 'assets/requirements.txt')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SportScrapper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.ico'],
)
app = BUNDLE(
    exe,
    name='SportScrapper.app',
    icon='assets/icon.ico',
    bundle_identifier=None,
)
