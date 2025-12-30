# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['COCK'],
    binaries=[],
    datas=[
        # Include icon
        ('resources/icons/icon.ico', 'resources/icons'),
        
        # Include splash screens
        ('resources/splash/splash_1.png', 'resources/splash'),
        ('resources/splash/splash_2.png', 'resources/splash'),
        ('resources/splash/splash_3.png', 'resources/splash'),
        ('resources/splash/splash_4.png', 'resources/splash'),

        # Include sounds
        ('resources/sounds/notification.wav', 'resources/sounds'),
        ('resources/sounds/prompt.wav', 'resources/sounds'),	
        
        # Include default data files (these will be templates in the exe)
        ('*.json', '.'),
    ],
    hiddenimports=[
        # looks for modules in the COCK subfolder
        'COCK.splash_screen',
        'COCK.path_manager',
        'COCK.config_loader',
        'COCK.clipboard_manager',
        'COCK.fast_detector',
        'COCK.message_optimizer',
        'COCK.mode_router',
        'COCK.overlay_manual',
        'COCK.settings_dialog',
        'COCK.shorthand_handler',
        'COCK.special_char_interspacing',
        'COCK.whitelist_manager',
        'COCK.fancy_text',
        'COCK.leet_speak',
        'COCK.filter_loader',
        'COCK.hotkey_handler',
        'COCK.permission_manager',
        'COCK.update_checker',
        'COCK.help_manager',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CompliantOnlineChatKit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                    # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/icon.ico',  # Embed icon in .exe
)
