"""
System Tray Integration Module
Provides Windows notification area icon, right-click context menu, and balloon notifications.
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt

from .autostart import is_autostart_enabled, set_autostart


class TrayIcon(QSystemTrayIcon):
    def __init__(self, main_window, engine, config_mgr, icon_path: str, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.engine = engine
        self.config_mgr = config_mgr
        self.icon_path = icon_path

        if icon_path:
            self.setIcon(QIcon(icon_path))

        self.setToolTip("Quick Expander - 全局文本自动补全 (运行中)")
        self._setup_menu()

        # Connect events: Single click or Double click reliably shows the window
        self.activated.connect(self._on_tray_activated)
        self.engine.on_status_changed = self._on_status_changed

    def _setup_menu(self):
        menu = QMenu()

        self.act_show = QAction("⚡ 显示管理面板", self)
        self.act_show.triggered.connect(self._show_window)
        menu.addAction(self.act_show)

        self.act_add = QAction("➕ 新增规则...", self)
        self.act_add.triggered.connect(self._add_rule)
        menu.addAction(self.act_add)

        menu.addSeparator()

        self.act_enabled = QAction("✔ 启用全局补全", self)
        self.act_enabled.setCheckable(True)
        self.act_enabled.setChecked(self.engine.is_enabled)
        self.act_enabled.triggered.connect(self._toggle_engine)
        menu.addAction(self.act_enabled)

        self.act_autostart = QAction("🚀 开机自动启动", self)
        self.act_autostart.setCheckable(True)
        self.act_autostart.setChecked(is_autostart_enabled())
        self.act_autostart.triggered.connect(self._toggle_autostart)
        menu.addAction(self.act_autostart)

        menu.addSeparator()

        self.act_reload = QAction("🔄 重新加载规则", self)
        self.act_reload.triggered.connect(self._reload_rules)
        menu.addAction(self.act_reload)

        self.act_quit = QAction("❌ 退出程序", self)
        self.act_quit.triggered.connect(self._quit_app)
        menu.addAction(self.act_quit)

        self.setContextMenu(menu)

    def _on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._show_window()

    def _show_window(self):
        self.main_window.show_and_activate()

    def _add_rule(self):
        self.main_window.show_and_activate()
        self.main_window._open_add_dialog()

    def _toggle_engine(self):
        self.engine.toggle_enabled()
        self.act_enabled.setChecked(self.engine.is_enabled)

    def _on_status_changed(self, is_enabled: bool):
        self.act_enabled.setChecked(is_enabled)
        state_str = "运行中" if is_enabled else "已暂停"
        self.setToolTip(f"Quick Expander - 全局文本自动补全 ({state_str})")
        if self.config_mgr.config.get("show_notification", True):
            self.showMessage(
                "Quick Expander",
                f"全局文本补全状态已切换为: 【{state_str}】\n按 {self.config_mgr.config.get('hotkey_toggle', 'Ctrl+Alt+S')} 可再次切换",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )

    def _toggle_autostart(self):
        current = self.act_autostart.isChecked()
        success = set_autostart(current)
        if success:
            self.config_mgr.config["autostart"] = current
            self.config_mgr.save_config()
            self.showMessage(
                "Quick Expander",
                "开机自动启动已" + ("开启" if current else "关闭"),
                QSystemTrayIcon.MessageIcon.Information,
                1500
            )
        else:
            self.act_autostart.setChecked(not current)

    def _reload_rules(self):
        self.config_mgr.snippets = self.config_mgr._load_snippets()
        self.main_window._refresh_table()
        self.showMessage(
            "Quick Expander",
            "规则库已重新加载！",
            QSystemTrayIcon.MessageIcon.Information,
            1500
        )

    def _quit_app(self):
        self.engine.stop()
        QApplication.instance().quit()
