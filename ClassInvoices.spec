# -*- mode: python ; coding: utf-8 -*-

import os
import sys

import wx
from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.datastruct import TOC
from PyInstaller.building.osx import BUNDLE

# Hack to be able to import app_config:
sys.path.insert(0, '.')

from app_config import APP_NAME, COPYRIGHT, APP_VERSION, APP_ID, APP_DESCRIPTION

one_file = True
block_cipher = None

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
             hiddenimports=['pythonjsonlogger.jsonlogger'],
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
    'debug': False,
    'bootloader_ignore_signals': False,
    'strip': False,
    'upx': True,
    'console': False,
}

is_mac = wx.GetOsVersion()[0] & wx.OS_MAC

is_windows = wx.GetOsVersion()[0] & wx.OS_WINDOWS
if is_windows:
    kwargs['version'] = 'installer/win_version_file.py'
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
    app = BUNDLE(exe,
                 TOC([('invoice-doc.icns', 'icons/invoice-doc.icns', 'DATA')]),
                 name='ClassInvoices.app',
                 icon='icons/app-icon-mac.icns',
                 bundle_identifier=APP_ID,
                 info_plist={
                     'NSPrincipleClass': 'NSApplication',
                     'NSAppleScriptEnabled': False,
                     'UTExportedTypeDeclarations': [
                         {
                             'UTTypeConformsTo': [
                                 'public.data',
                             ],
                             'UTTypeDescription': 'ClassInvoices Document',
                             'UTTypeIdentifier': APP_ID + '.classinvoice',
                             'UTTypeIconFile': 'invoice-doc.icns',
                             'UTTypeTagSpecification': {
                                 'public.filename-extension': [
                                     'classinvoice',
                                 ],
                                 'public.mime-type': 'application/octet-stream',
                             }
                         }
                     ],
                     'CFBundleDocumentTypes': [
                         {
                             'CFBundleTypeIconFile': 'invoice-doc.icns',
                             'CFBundleTypeName': 'ClassInvoices',
                             'CFBundleTypeRole': 'Editor',
                             'LSHandlerRank': 'Owner',
                             'LSItemContentTypes': [APP_ID + '.classinvoice'],
                         }
                     ],
                     'CFBundleName': APP_NAME,
                     'CFBundleDisplayName': APP_NAME,
                     'CFBundleGetInfoString': APP_DESCRIPTION,
                     'CFBundleIdentifier': APP_ID,
                     'CFBundleVersion': APP_VERSION,
                     'CFBundleShortVersionString': APP_VERSION,
                     'NSHumanReadableCopyright': COPYRIGHT,
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
