# -*- mode: python ; coding: utf-8 -*-

import os

import wx
# These imports are not needed, but they let IntelliJ know where they are so it can resolve them.
from PyInstaller.building.api import EXE, PYZ, COLLECT
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.datastruct import TOC
from PyInstaller.building.osx import BUNDLE

one_file = True
block_cipher = None
debug = False
windowed = True

is_mac = wx.GetOsVersion()[0] & wx.OS_MAC
is_windows = wx.GetOsVersion()[0] & wx.OS_WINDOWS

# Find where rml fonts are so we can copy them to the runtime. The z3c.rml library
# tries to load these and the import fails if they are not found.
fonts_dir = None
for d in [
    'venv/lib/python3.7/site-packages/reportlab/fonts',
    'venv/lib/python3.6/site-packages/reportlab/fonts',
    'venv/Lib/site-packages/reportlab/fonts',
]:
    if os.path.isdir(d):
        fonts_dir = d
        break

datas = [
    (os.path.join(fonts_dir, 'Vera.ttf'), 'reportlab/fonts'),
    (os.path.join(fonts_dir, 'VeraBI.ttf'), 'reportlab/fonts'),
    (os.path.join(fonts_dir, 'VeraBd.ttf'), 'reportlab/fonts'),
    (os.path.join(fonts_dir, 'VeraIt.ttf'), 'reportlab/fonts'),
]

a = Analysis(['ClassInvoices.py'],
             binaries=[],
             datas=datas,
             hiddenimports=[],
             hookspath=['installer'],
             runtime_hooks=[],
             excludes=['tkinter'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False,
             )
pyz = PYZ(a.pure,
          a.zipped_data,
          cipher=block_cipher,
          )

kwargs = {
    'name': 'ClassInvoices',
    'debug': debug,
    'bootloader_ignore_signals': False,
    'strip': False,
    'upx': True,
    'console': not windowed,
}

if is_windows:
    kwargs['version'] = 'build/win_version_file.py'
    kwargs['icon'] = 'icons/app-icon-win.ico'
elif is_mac:
    kwargs['icon'] = 'icons/app-icon-mac.icns'

if one_file or is_mac:
    exe = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              [],
              runtime_tmpdir=None,
              **kwargs)
else:
    exe = EXE(pyz,
              a.scripts,
              [],
              exclude_binaries=True,
              **kwargs)

if is_mac:
    # Hack to be able to import app_config:
    import sys
    sys.path.insert(0, '.')
    import app_config
    app = BUNDLE(exe,
                 # Copy tho document icon to the Resources dir in the app
                 # bundle; it is referenced in the Info.plist below.
                 TOC([('invoice-doc.icns', 'icons/invoice-doc.icns', 'DATA')]),
                 name='ClassInvoices.app',
                 icon='icons/app-icon-mac.icns',
                 bundle_identifier=app_config.APP_ID,
                 info_plist={
                     'NSPrincipleClass': 'NSApplication',
                     'NSAppleScriptEnabled': False,
                     'UTExportedTypeDeclarations': [
                         {
                             'UTTypeConformsTo': [
                                 'public.data',
                             ],
                             'UTTypeDescription': 'ClassInvoices Document',
                             'UTTypeIdentifier': app_config.APP_ID + '.classinvoice',
                             'UTTypeIconFile': 'invoice-doc.icns',
                             'UTTypeTagSpecification': {
                                 'public.filename-extension': [
                                     'classinvoice',
                                 ],
                                 'public.mime-type': 'application/octet-stream',
                             },
                         },
                     ],
                     'CFBundleDocumentTypes': [
                         {
                             'CFBundleTypeIconFile': 'invoice-doc.icns',
                             'CFBundleTypeName': 'ClassInvoices',
                             'CFBundleTypeRole': 'Editor',
                             'LSHandlerRank': 'Owner',
                             'LSItemContentTypes': [app_config.APP_ID + '.classinvoice'],
                         },
                     ],
                     'CFBundleName': app_config.APP_NAME,
                     'CFBundleDisplayName': app_config.APP_NAME,
                     'CFBundleGetInfoString': app_config.APP_DESCRIPTION,
                     'CFBundleIdentifier': app_config.APP_ID,
                     'CFBundleVersion': app_config.APP_VERSION,
                     'CFBundleShortVersionString': app_config.APP_VERSION,
                     'NSHumanReadableCopyright': app_config.APP_COPYRIGHT,
                 },
                 )
else:
    # For Windows and Linux
    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=True,
                   name='ClassInvoices')
