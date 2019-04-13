# -*- mode: python ; coding: utf-8 -*-

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

# For Windows
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
          icon='installer/invoice.ico',
          )

# For Mac OS X
app = BUNDLE(exe,
             name='ClassInvoices.app',
             icon='installer/invoice.ico',
             bundle_identifier=None,
             )
