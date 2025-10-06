# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for deploy-4-developer
Supports: Windows, Linux, macOS
"""
import sys
import os
from pathlib import Path

# Project configuration
PACKAGE_NAME = 'deploy-4-developer'
EXECUTABLE_NAME = 'deploy4dev'
VERSION = '0.0.1'

# Entry point
main_script = 'src/deploy_4_developer/cli/deploy.py'

# Paths
src_path = Path('src')
package_path = src_path / 'deploy_4_developer'

# Collect data files (if any configuration files, templates, etc.)
datas = []

# Example: Include README or other resources (optional)
if Path('README.md').exists():
    datas.append(('README.md', '.'))

# Binary files (platform-specific crypto libraries)
binaries = []

# Hidden imports (modules that PyInstaller might miss)
hiddenimports = [
    'deploy_4_developer',
    'deploy_4_developer.cli',
    'deploy_4_developer.cli.deploy',
    'deploy_4_developer.cli.sys_util',
    
    # Core dependencies
    'paramiko',
    'paramiko.transport',
    'paramiko.client',
    'paramiko.rsakey',
    'paramiko.dsskey',
    'paramiko.ecdsakey',
    'paramiko.ed25519key',
    'paramiko.ssh_exception',
    'paramiko.sftp_client',
    'paramiko.channel',
    'paramiko.config',
    'paramiko.hostkeys',
    
    # Paramiko dependencies
    'cryptography',
    'cryptography.hazmat',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.backends',
    'cryptography.hazmat.backends.openssl',
    'bcrypt',
    'nacl',
    'nacl.signing',
    'nacl.public',
    
    # Standard library modules that might be missed
    'argparse',
    'getpass',
    'json',
    'logging',
    'os',
    'pathlib',
    'subprocess',
]

# Exclude unnecessary modules to reduce size
excludes = [
    # GUI frameworks
    'tkinter',
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    'wx',
    
    # Large libraries not needed
    'numpy',
    'pandas',
    'matplotlib',
    'scipy',
    'PIL',
    'cv2',
    'torch',
    'tensorflow',
    'sklearn',
    
    # Development/testing tools
    'pytest',
    'unittest',
    'IPython',
    'jupyter',
    'notebook',
    'pdb',
    'doctest',
    
    # Web frameworks
    'flask',
    'django',
    'aiohttp',
    'fastapi',
    
    # Database
    'sqlite3',
    'sqlalchemy',
    'psycopg2',
    'pymongo',
]

block_cipher = None

a = Analysis(
    [main_script],
    pathex=[str(src_path)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=2,  # Python bytecode optimization level (0, 1, 2)
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Platform-specific executable configuration
if sys.platform == 'win32':
    # Windows executable
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=EXECUTABLE_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,  # Console application
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,  # Add .ico file path if you have one
    )
elif sys.platform == 'darwin':
    # macOS executable
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=EXECUTABLE_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    
    # Optional: Create macOS app bundle
    app = BUNDLE(
        exe,
        name=f'{EXECUTABLE_NAME}.app',
        icon=None,  # Add .icns file path if you have one
        bundle_identifier=f'com.bytebiscuit.{PACKAGE_NAME}',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': VERSION,
        },
    )
else:
    # Linux executable
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=EXECUTABLE_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=True,  # Strip symbols on Linux
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

# Alternative: COLLECT mode (creates a folder with all dependencies)
# Uncomment the following if you prefer a directory distribution instead of a single executable
"""
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=EXECUTABLE_NAME
)
"""
