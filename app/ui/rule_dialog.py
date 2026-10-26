"""
Rule Editor Dialog
Modal dialog for creating and editing snippet expansion rules, including category assignment.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QCheckBox, QComboBox,
    QGroupBox, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from ..variables import resolve_variables


class RuleDialog(QDialog):
    def __init__(self, parent=None, rule_data: dict = None, categories: list[str] = None):
        super().__init__(parent)
        self.rule_data = rule_data or {}
        self.is_edit = bool(rule_data)
        self.categories = categories or ["快捷编码", "个人信息", "工作模版", "动态宏"]
        self.setWindowTitle("编辑扩展规则" if self.is_edit else "新增扩展规则")
        self.resize(580, 660)
        self.setModal(True)

        self._setup_ui()
        self._load_data()
        self._update_preview()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Trigger input & Category selection row
        row_top = QHBoxLayout()
        row_top.setSpacing(12)

        # Trigger
        v_trig = QVBoxLayout()
        lbl_trig = QLabel("触发词 (Trigger)*:")
        lbl_trig.setStyleSheet("font-weight: bold;")
        self.edit_trigger = QLineEdit()
        self.edit_trigger.setPlaceholderText("例如: 411, @@em, //date 等")
        self.edit_trigger.textChanged.connect(self._update_preview)
        v_trig.addWidget(lbl_trig)
        v_trig.addWidget(self.edit_trigger)
        row_top.addLayout(v_trig, 2)

        # Category
        v_cat = QVBoxLayout()
        lbl_cat = QLabel("所属分类 (Category):")
        lbl_cat.setStyleSheet("font-weight: bold;")
        self.combo_category = QComboBox()
        self.combo_category.setEditable(True)
        for cat in self.categories:
            self.combo_category.addItem(cat)
        v_cat.addWidget(lbl_cat)
        v_cat.addWidget(self.combo_category)
        row_top.addLayout(v_cat, 1)

        layout.addLayout(row_top)

        # 2. Replacement input & Variable buttons
        lbl_repl = QLabel("替换为内容 (Replacement)*:")
        lbl_repl.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl_repl)

        # Quick variable helper buttons
        var_box = QHBoxLayout()
        var_box.setSpacing(6)

        vars_map = [
            ("📅 日期", "{{date}}"),
            ("⏰ 时间", "{{time}}"),
            ("📆 完整时间", "{{datetime}}"),
            ("📋 剪贴板", "{{clipboard}}"),
            ("🎯 光标位置", "{{cursor}}"),
            ("🔑 UUID", "{{uuid}}"),
        ]

        for label, tag in vars_map:
            btn = QPushButton(label)
            btn.setStyleSheet("font-size: 11px; padding: 3px 8px;")
            btn.clicked.connect(lambda _, t=tag: self._insert_variable(t))
            var_box.addWidget(btn)
        
        layout.addLayout(var_box)

        self.edit_replacement = QPlainTextEdit()
        self.edit_replacement.setPlaceholderText("输入要自动替换补全的完整内容，例如: 4113293000 或多行文本模版...")
        self.edit_replacement.textChanged.connect(self._update_preview)
        layout.addWidget(self.edit_replacement)

        # 3. Live Preview
        preview_group = QGroupBox("实时预览 (Live Preview)")
        preview_layout = QVBoxLayout(preview_group)
        self.lbl_preview = QLabel("等待输入...")
        self.lbl_preview.setWordWrap(True)
        self.lbl_preview.setStyleSheet("color: #89b4fa; font-family: monospace; padding: 4px;")
        preview_layout.addWidget(self.lbl_preview)
        layout.addWidget(preview_group)

        # 4. Settings (Mode & Method)
        settings_layout = QHBoxLayout()
        
        # Trigger mode
        mode_layout = QVBoxLayout()
        mode_layout.addWidget(QLabel("触发模式:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItem("⚡ 即时触发 (输入完成立刻替换)", "instant")
        self.combo_mode.addItem("⌨️ 触发键触发 (按空格/回车后替换)", "trigger_key")
        mode_layout.addWidget(self.combo_mode)
        settings_layout.addLayout(mode_layout)

        # Injection method
        method_layout = QVBoxLayout()
        method_layout.addWidget(QLabel("注入方式:"))
        self.combo_method = QComboBox()
        self.combo_method.addItem("🤖 智能自适应 (推荐)", "auto")
        self.combo_method.addItem("⌨️ 按键模拟 (SendInput)", "sendinput")
        self.combo_method.addItem("📋 剪贴板闪电粘贴", "clipboard")
        method_layout.addWidget(self.combo_method)
        settings_layout.addLayout(method_layout)

        layout.addLayout(settings_layout)

        # 5. Description & Checkboxes
        lbl_desc = QLabel("规则说明/备注 (可选):")
        self.edit_desc = QLineEdit()
        self.edit_desc.setPlaceholderText("例如: 公司内部编码 / 财务专号")
        layout.addWidget(lbl_desc)
        layout.addWidget(self.edit_desc)

        chk_layout = QHBoxLayout()
        self.chk_match_case = QCheckBox("严格区分大小写 (Match Case)")
        self.chk_match_case.setChecked(True)
        self.chk_enabled = QCheckBox("启用此规则 (Enabled)")
        self.chk_enabled.setChecked(True)
        chk_layout.addWidget(self.chk_match_case)
        chk_layout.addWidget(self.chk_enabled)
        chk_layout.addStretch()
        layout.addLayout(chk_layout)

        # 6. Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("保存规则")
        self.btn_save.setObjectName("btnPrimary")
        self.btn_save.clicked.connect(self._on_save)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def _insert_variable(self, tag: str):
        cursor = self.edit_replacement.textCursor()
        cursor.insertText(tag)
        self.edit_replacement.setTextCursor(cursor)
        self.edit_replacement.setFocus()

    def _load_data(self):
        if not self.is_edit:
            return
        self.edit_trigger.setText(self.rule_data.get("trigger", ""))
        self.edit_replacement.setPlainText(self.rule_data.get("replacement", ""))
        self.edit_desc.setText(self.rule_data.get("description", ""))
        self.chk_match_case.setChecked(self.rule_data.get("match_case", True))
        self.chk_enabled.setChecked(self.rule_data.get("enabled", True))

        # Category
        cat = self.rule_data.get("category", "快捷编码")
        idx_cat = self.combo_category.findText(cat)
        if idx_cat >= 0:
            self.combo_category.setCurrentIndex(idx_cat)
        else:
            self.combo_category.setEditText(cat)

        mode = self.rule_data.get("mode", "instant")
        idx_mode = self.combo_mode.findData(mode)
        if idx_mode >= 0:
            self.combo_mode.setCurrentIndex(idx_mode)

        method = self.rule_data.get("method", "auto")
        idx_method = self.combo_method.findData(method)
        if idx_method >= 0:
            self.combo_method.setCurrentIndex(idx_method)

    def _update_preview(self):
        raw = self.edit_replacement.toPlainText()
        if not raw:
            self.lbl_preview.setText("（暂无内容）")
            return
        resolved, _ = resolve_variables(raw)
        self.lbl_preview.setText(resolved)

    def _on_save(self):
        trigger = self.edit_trigger.text().strip()
        replacement = self.edit_replacement.toPlainText()
        category = self.combo_category.currentText().strip() or "快捷编码"
        
        if not trigger:
            QMessageBox.warning(self, "输入错误", "触发词不能为空！")
            self.edit_trigger.setFocus()
            return
        if not replacement:
            QMessageBox.warning(self, "输入错误", "替换内容不能为空！")
            self.edit_replacement.setFocus()
            return

        self.result_data = {
            "trigger": trigger,
            "replacement": replacement,
            "description": self.edit_desc.text().strip(),
            "category": category,
            "match_case": self.chk_match_case.isChecked(),
            "enabled": self.chk_enabled.isChecked(),
            "mode": self.combo_mode.currentData(),
            "method": self.combo_method.currentData(),
        }
        self.accept()

    def get_data(self) -> dict:
        return getattr(self, "result_data", {})
