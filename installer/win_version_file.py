# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx

from app_config import APP_VERSION, COPYRIGHT, APP_NAME, APP_DESCRIPTION, APP_AUTHOR, APP_VERSION_TUPLE

VSVersionInfo(
    ffi=FixedFileInfo(
        # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
        # Set not needed items to zero 0.
        filevers=APP_VERSION_TUPLE,
        prodvers=APP_VERSION_TUPLE,
        # Contains a bitmask that specifies the valid bits 'flags'r
        mask=0x3f,
        # Contains a bitmask that specifies the Boolean attributes of the file.
        flags=0x0,
        # The operating system for which this file was designed.
        # 0x4 - NT and there is no need to change it.
        OS=0x40004,
        # The general type of file.
        # 0x1 - the file is an application.
        fileType=0x1,
        # The function of the file.
        # 0x0 - the function is not defined for this fileType
        subtype=0x0,
        # Creation date and time stamp.
        date=(23730, 36814)
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    '040904B0',
                    [StringStruct('CompanyName', APP_AUTHOR),
                     StringStruct('FileDescription', APP_DESCRIPTION),
                     StringStruct('FileVersion', APP_VERSION),
                     StringStruct('InternalName', f'{APP_NAME}.exe'),
                     StringStruct('LegalCopyright', COPYRIGHT),
                     StringStruct('OriginalFilename', f'{APP_NAME}.exe'),
                     StringStruct('ProductName', APP_NAME),
                     StringStruct('ProductVersion', APP_VERSION)])
            ]),
        VarFileInfo([VarStruct('Translation', [1033, 1200])])
    ]
)
