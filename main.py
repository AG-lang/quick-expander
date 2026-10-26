"""
Quick Expander - Main Entry Point
Launches the PyQt6 GUI application, system tray icon, and global keyboard expansion engine.
Includes crash logger, single-instance IPC, and robust window activation.
"""

import sys
import os
import argparse
import traceback
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Crash logger wrapper
def log_crash(e_type, e_value, e_tb):
    error_msg = "".join(traceback.format_exception(e_type, e_value, e_tb))
    print(error_msg)
    try:
        log_file = BASE_DIR / "error.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n--- CRASH AT {os.path.basename(__file__)} ---\n")
            f.write(error_msg)
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, f"程序启动发生错误:\n\n{error_msg[:600]}", "Quick Expander 错误", 0x10)
    except Exception:
        pass

sys.excepthook = log_crash

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from app.config import ConfigManager
from app.engine import ExpansionEngine
from app.ui.main_window import MainWindow
from app.tray import TrayIcon

IPC_SERVER_NAME = "QuickExpander_SingleInstance_IPC_v1"


def send_show_command_to_existing_instance() -> bool:
    """Checks if another instance is already running. If so, tells it to show its window."""
    socket = QLocalSocket()
    socket.connectToServer(IPC_SERVER_NAME)
    if socket.waitForConnected(400):
        try:
            socket.write(b"SHOW\n")
            socket.waitForBytesWritten(400)
            socket.disconnectFromServer()
            return True
        except Exception:
            return False
    return False


def setup_ipc_server(main_window: MainWindow) -> QLocalServer:
    """Sets up local IPC server to listen for commands from subsequent launches."""
    QLocalServer.removeServer(IPC_SERVER_NAME)
    server = QLocalServer()
    if not server.listen(IPC_SERVER_NAME):
        print(f"[IPC] Notice: Server listen on {IPC_SERVER_NAME} status: False")

    def on_new_connection():
        while server.hasPendingConnections():
            client = server.nextPendingConnection()
            if not client:
                continue

            def make_reader(c):
                def on_ready_read():
                    try:
                        data = bytes(c.readAll()).decode("utf-8").strip()
                        if "SHOW" in data:
                            main_window.show_and_activate()
                    except Exception as e:
                        print(f"[IPC] Error reading command: {e}")
                return on_ready_read

            client.readyRead.connect(make_reader(client))

    server.newConnection.connect(on_new_connection)
    return server


def main():
    parser = argparse.ArgumentParser(description="Quick Expander - Global Text Expansion Tool")
    parser.add_argument("--minimized", action="store_true", help="Start minimized to system tray")
    args = parser.parse_args()

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("QuickExpander")
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray when window is closed

    # Single-instance check via IPC: if already running, wake up and exit
    if send_show_command_to_existing_instance():
        sys.exit(0)

    # Icon path
    icon_ico = BASE_DIR / "assets" / "icon.ico"
    icon_png = BASE_DIR / "assets" / "icon.png"
    icon_path = str(icon_ico if icon_ico.exists() else icon_png)

    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    # Initialize Core Managers
    config_mgr = ConfigManager()
    engine = ExpansionEngine(config_mgr)

    # Initialize UI & Tray
    main_window = MainWindow(config_mgr, engine, icon_path=icon_path)
    tray_icon = TrayIcon(main_window, engine, config_mgr, icon_path=icon_path)
    tray_icon.show()

    # Setup IPC Server on the main instance
    ipc_server = setup_ipc_server(main_window)

    # Show main window immediately if not minimized
    start_minimized = args.minimized or config_mgr.config.get("start_minimized", False)
    if not start_minimized:
        main_window.show_and_activate()

    # Start keyboard hook engine
    engine.start()

    # Execute Qt main event loop
    exit_code = app.exec()

    # Clean shutdown
    engine.stop()
    QLocalServer.removeServer(IPC_SERVER_NAME)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
