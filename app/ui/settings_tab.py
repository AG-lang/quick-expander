"""
Settings Tab Widget
Manages application configuration, autostart, hotkeys, theme, and data import/export.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QSpinBox, QComboBox,
    QGroupBox, QFileDialog, QMessageBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..autostart import is_autostart_enabled, set_autostart


class SettingsTab(QWidget):
    theme_changed = pyqtSignal(str)
    hotkey_changed = pyqtSignal(str)
    settings_updated = pyqtSignal()
    data_reloaded = pyqtSignal()

    def __init__(self, config_mgr, engine, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.engine = engine
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)
        layout.setContentsMargins(10, 10, 10, 10)

        # 1. System & Startup Group
        group_system = QGroupBox("🚀 系统与常规设置")
        sys_layout = QVBoxLayout(group_system)
        sys_layout.setSpacing(10)

        self.chk_autostart = QCheckBox("开机自动启动 (后台静默常驻系统托盘)")
        self.chk_autostart.toggled.connect(self._on_autostart_toggled)
        sys_layout.addWidget(self.chk_autostart)

        self.chk_start_minimized = QCheckBox("启动时直接最小化到托盘 (不弹出主界面)")
        self.chk_start_minimized.toggled.connect(self._save_settings)
        sys_layout.addWidget(self.chk_start_minimized)

        # Hotkey setting
        hotkey_box = QHBoxLayout()
        hotkey_box.addWidget(QLabel("全局暂停/恢复热键:"))
        self.edit_hotkey = QLineEdit()
        self.edit_hotkey.setPlaceholderText("<ctrl>+<alt>+s")
        hotkey_box.addWidget(self.edit_hotkey)
        
        btn_apply_hotkey = QPushButton("应用热键")
        btn_apply_hotkey.clicked.connect(self._on_apply_hotkey)
        hotkey_box.addWidget(btn_apply_hotkey)
        sys_layout.addLayout(hotkey_box)

        # Theme selection
        theme_box = QHBoxLayout()
        theme_box.addWidget(QLabel("界面主题 (Theme):"))
        self.combo_theme = QComboBox()
        self.combo_theme.addItem("🌙 深色模式 (Dark)", "dark")
        self.combo_theme.addItem("☀️ 浅色模式 (Light)", "light")
        self.combo_theme.currentIndexChanged.connect(self._on_theme_changed)
        theme_box.addWidget(self.combo_theme)
        theme_box.addStretch()
        sys_layout.addLayout(theme_box)

        layout.addWidget(group_system)

        # 2. Performance & Behavior Group
        group_behavior = QGroupBox("⚙️ 扩展行为与性能调节")
        beh_layout = QVBoxLayout(group_behavior)
        beh_layout.setSpacing(10)

        self.chk_sound = QCheckBox("每次成功补全时播放提示音 (Beep)")
        self.chk_sound.toggled.connect(self._save_settings)
        beh_layout.addWidget(self.chk_sound)

        # Delay spinbox
        delay_box = QHBoxLayout()
        delay_box.addWidget(QLabel("退格消除安全延迟 (毫秒):"))
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(0, 100)
        self.spin_delay.setValue(10)
        self.spin_delay.setSuffix(" ms")
        self.spin_delay.valueChanged.connect(self._save_settings)
        delay_box.addWidget(self.spin_delay)
        
        lbl_hint = QLabel("(针对较慢的旧应用可适当调大，如 15ms)")
        lbl_hint.setStyleSheet("color: #a6adc8; font-size: 11px;")
        delay_box.addWidget(lbl_hint)
        delay_box.addStretch()
        beh_layout.addLayout(delay_box)

        layout.addWidget(group_behavior)

        # 3. Data Backup & Import/Export
        group_data = QGroupBox("💾 规则备份与导入导出")
        data_layout = QVBoxLayout(group_data)
        data_layout.setSpacing(10)

        btn_row1 = QHBoxLayout()
        btn_exp_json = QPushButton("📤 导出 JSON 备份")
        btn_exp_json.clicked.connect(self._export_json)
        btn_imp_json = QPushButton("📥 导入 JSON 规则")
        btn_imp_json.clicked.connect(self._import_json)
        btn_row1.addWidget(btn_exp_json)
        btn_row1.addWidget(btn_imp_json)
        data_layout.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        btn_exp_csv = QPushButton("📊 导出 Excel/CSV 表格")
        btn_exp_csv.clicked.connect(self._export_csv)
        btn_imp_csv = QPushButton("📑 导入 CSV 表格")
        btn_imp_csv.clicked.connect(self._import_csv)
        btn_row2.addWidget(btn_exp_csv)
        btn_row2.addWidget(btn_imp_csv)
        data_layout.addLayout(btn_row2)

        layout.addWidget(group_data)

        # 4. Quick Help / Variable Cheatsheet
        group_help = QGroupBox("📖 动态变量速查表 (Macro Cheatsheet)")
        help_layout = QVBoxLayout(group_help)
        help_text = (
            "<b>{{date}}</b> : 当前日期 (如 2026-08-27)<br>"
            "<b>{{time}}</b> : 当前时间 (如 14:30:00)<br>"
            "<b>{{datetime}}</b> : 完整时间 (如 2026-08-27 14:30:00)<br>"
            "<b>{{weekday}}</b> : 当前星期 (如 星期四)<br>"
            "<b>{{clipboard}}</b> : 插入当前剪贴板文本<br>"
            "<b>{{uuid}}</b> : 生成随机 UUID4 唯一码<br>"
            "<b>{{cursor}}</b> : 补全后光标自动定位的目标位置<br>"
            "<b>{{date:%Y/%m/%d}}</b> : 自定义日期时间格式"
        )
        lbl_cheatsheet = QLabel(help_text)
        lbl_cheatsheet.setStyleSheet("line-height: 140%; color: #89b4fa;")
        help_layout.addWidget(lbl_cheatsheet)
        layout.addWidget(group_help)

        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _load_settings(self):
        cfg = self.config_mgr.config
        self.chk_autostart.setChecked(is_autostart_enabled())
        self.chk_start_minimized.setChecked(cfg.get("start_minimized", False))
        self.edit_hotkey.setText(cfg.get("hotkey_toggle", "<ctrl>+<alt>+s"))
        self.chk_sound.setChecked(cfg.get("play_sound", False))
        self.spin_delay.setValue(cfg.get("backspace_delay_ms", 10))

        theme = cfg.get("theme", "dark")
        idx = self.combo_theme.findData(theme)
        if idx >= 0:
            self.combo_theme.setCurrentIndex(idx)

    def _save_settings(self):
        cfg = self.config_mgr.config
        cfg["start_minimized"] = self.chk_start_minimized.isChecked()
        cfg["play_sound"] = self.chk_sound.isChecked()
        cfg["backspace_delay_ms"] = self.spin_delay.value()
        self.config_mgr.save_config()
        self.settings_updated.emit()

    def _on_autostart_toggled(self, checked: bool):
        success = set_autostart(checked)
        if success:
            self.config_mgr.config["autostart"] = checked
            self.config_mgr.save_config()
        else:
            QMessageBox.warning(self, "错误", "设置开机自启动失败，请检查权限！")
            self.chk_autostart.setChecked(not checked)

    def _on_apply_hotkey(self):
        key_str = self.edit_hotkey.text().strip()
        if not key_str:
            QMessageBox.warning(self, "错误", "热键不能为空！")
            return
        self.engine.update_hotkey(key_str)
        self.hotkey_changed.emit(key_str)
        QMessageBox.information(self, "成功", f"全局热键已更新为: {key_str}")

    def _on_theme_changed(self):
        theme = self.combo_theme.currentData()
        self.config_mgr.config["theme"] = theme
        self.config_mgr.save_config()
        self.theme_changed.emit(theme)

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出规则为 JSON", "snippets_backup.json", "JSON 文件 (*.json)")
        if path:
            try:
                self.config_mgr.export_json(path)
                QMessageBox.information(self, "成功", f"规则已成功导出到:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出失败: {e}")

    def _import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "从 JSON 导入规则", "", "JSON 文件 (*.json)")
        if path:
            res = QMessageBox.question(
                self, "导入模式", "是否覆盖现有全部规则？\n点击【Yes/是】完全覆盖，点击【No/否】追加合并。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if res == QMessageBox.StandardButton.Cancel:
                return
            overwrite = (res == QMessageBox.StandardButton.Yes)
            try:
                count = self.config_mgr.import_json(path, overwrite=overwrite)
                self.data_reloaded.emit()
                QMessageBox.information(self, "导入成功", f"已成功导入 {count} 条规则！")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", f"导入失败: {e}")

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出规则为 CSV", "snippets.csv", "CSV 表格 (*.csv)")
        if path:
            try:
                self.config_mgr.export_csv(path)
                QMessageBox.information(self, "成功", f"规则已成功导出到:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出失败: {e}")

    def _import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "从 CSV 导入规则", "", "CSV 表格 (*.csv)")
        if path:
            res = QMessageBox.question(
                self, "导入模式", "是否覆盖现有全部规则？\n点击【Yes/是】完全覆盖，点击【No/否】追加合并。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if res == QMessageBox.StandardButton.Cancel:
                return
            overwrite = (res == QMessageBox.StandardButton.Yes)
            try:
                count = self.config_mgr.import_csv(path, overwrite=overwrite)
                self.data_reloaded.emit()
                QMessageBox.information(self, "导入成功", f"已成功导入 {count} 条规则！")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", f"导入失败: {e}")
