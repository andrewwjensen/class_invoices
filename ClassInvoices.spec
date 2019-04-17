# -*- mode: python ; coding: utf-8 -*-
import os

one_file = True
block_cipher = None

for d in [
    'venv/lib/python3.7/site-packages/reportlab/fonts',
    'venv/lib/python3.6/site-packages/reportlab/fonts',
    'venv/Lib/site-packages/reportlab/fonts',
]:
    if os.path.isdir(d):
        fonts_dir = d
        break
else:
    fonts_dir = 'fonts'

a = Analysis(['ClassInvoices.py'],
             binaries=[],
             datas=[
                 (os.path.join(fonts_dir, 'Vera.ttf'), 'reportlab/fonts'),
                 (os.path.join(fonts_dir, 'VeraBI.ttf'), 'reportlab/fonts'),
                 (os.path.join(fonts_dir, 'VeraBd.ttf'), 'reportlab/fonts'),
                 (os.path.join(fonts_dir, 'VeraIt.ttf'), 'reportlab/fonts'),
             ],
             hiddenimports=['pythonjsonlogger.jsonlogger'],
             hookspath=['installer'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False,
             )
pyz = PYZ(a.pure,
          a.zipped_data,
          cipher=block_cipher,
          )

if one_file:
    exe = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              [],
              name='ClassInvoices',
              debug=False,
              bootloader_ignore_signals=False,
              strip=False,
              upx=True,
              runtime_tmpdir=None,
              console=False,
              version='installer/win_version_file.py',
              icon='icons/app-icon-win.ico',
              )
else:
    exe = EXE(pyz,
              a.scripts,
              [],
              exclude_binaries=True,
              name='ClassInvoices',
              debug=False,
              bootloader_ignore_signals=False,
              strip=False,
              upx=True,
              console=False,
              version='installer/win_version_file.py',
              icon='icons/app-icon-win.ico',
              )
    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=True,
                   name='ClassInvoices')

# For Mac OS X
app = BUNDLE(exe,
             name='ClassInvoices.app',
             icon='icons/app-icon-mac.icns',
             bundle_identifier='com.thejensenfam.classinvoices',
             info_plist={
                 'NSPrincipleClass': 'NSApplication',
                 'NSAppleScriptEnabled': False,
                 'CFBundleDocumentTypes': [
                     {
                         'CFBundleTypeName': 'ClassInvoices',
                         'CFBundleTypeIconFiles': [
                             'icons/invoice-16x16.png',
                             'icons/invoice-24x24.png',
                             'icons/invoice-32x32.png',
                             'icons/invoice-64x64.png',
                             'icons/invoice-128x128.png',
                             'icons/invoice-256x256.png',
                             'icons/invoice-512x512.png',
                         ],
                         'CFBundleTypeRole': 'Viewer',
                         'LSItemContentTypes': ['com.thenjensenfam.classinvoices'],
                         'LSHandlerRank': 'Owner'
                     }
                 ]
             },
             )
