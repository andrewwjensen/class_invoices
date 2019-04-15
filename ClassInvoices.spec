# -*- mode: python ; coding: utf-8 -*-

one_file = False

block_cipher = None

a = Analysis(['ClassInvoices.py'],
             binaries=[],
             datas=[
                 ('venv/Lib/site-packages/reportlab/fonts/Vera.ttf', 'reportlab/fonts'),
                 ('venv/Lib/site-packages/reportlab/fonts/VeraBI.ttf', 'reportlab/fonts'),
                 ('venv/Lib/site-packages/reportlab/fonts/VeraBd.ttf', 'reportlab/fonts'),
                 ('venv/Lib/site-packages/reportlab/fonts/VeraIt.ttf', 'reportlab/fonts'),
             ],
             hiddenimports=[],
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
              icon='icons/invoice.ico',
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
              icon='icons/invoice.ico',
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
             icon='icons/invoice.ico',
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
