# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('config', 'config'), ('assests/icons', 'icons'), ('assests', 'assests')],
    hiddenimports=['ui_components', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtNetwork', 'PyQt5.QtMultimedia', 'PyQt5.QtMultimediaWidgets', 'PyQt5.QtPrintSupport', 'DeviceSettings', 'AdvancedCamera', 'config_manager', 'background_service', 'google_drive_manager', 'recordings_page', 'recording_manager', 'stream_manager', 'enhanced_camera_manager', 'enhanced_fullscreen_widget', 'enhanced_review_system', 'fire_detection_backend', 'notification_manager', 'alerts_manager', 'cloud_backup_manager', 'user_managers', 'voice_command_manager', 'splash_screen'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tensorflow', 'tensorboard', 'onnx', 'onnxruntime', 'openvino'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='firevision',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assests\\logo\\fv_logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='firevision',
)
