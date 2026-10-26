"""
Main Application Window
Provides full GUI management for rules, categories sidebar, real-time interactive testing sandbox,
metrics display, settings integration, and candidate popup binding.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QFrame, QMessageBox, QMenu,
    QPlainTextEdit, QCheckBox, QAbstractItemView, QApplication,
    QListWidget, QListWidgetItem, QInputDialog, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QIcon, QFont, QAction, QColor, QCursor

from .rule_dialog import RuleDialog
from .settings_tab import SettingsTab
from .candidate_popup import CandidatePopup
from .styles import DARK_THEME, LIGHT_THEME
from ..config import ConfigManager
from ..engine import ExpansionEngine


class MainWindow(QMainWindow):
    # Signals for cross-thread UI updates
    rule_triggered_signal = pyqtSignal(dict, str)
    status_changed_signal = pyqtSignal(bool)
    show_candidates_signal = pyqtSignal(list, str)
    hide_candidates_signal = pyqtSignal()

    def __init__(self, config_mgr: ConfigManager, engine: ExpansionEngine, icon_path: str = None):
        super().__init__()
        self.config_mgr = config_mgr
        self.engine = engine
        self.icon_path = icon_path
        self.current_category = "全部"

        self.setWindowTitle("Quick Expander - 全局文本自动补全与扩展神器")
        self.resize(1060, 720)

        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        # Center on screen
        self._center_on_screen()

        # Candidate Popup Floating Widget
        self.candidate_popup = CandidatePopup()
        self.candidate_popup.candidate_chosen.connect(self.engine.select_candidate_direct)

        # Setup engine callbacks
        self.engine.on_expanded = lambda s, r: self.rule_triggered_signal.emit(s, r)
        self.engine.on_status_changed = lambda st: self.status_changed_signal.emit(st)
        self.engine.on_show_candidates = lambda c, t: self.show_candidates_signal.emit(c, t)
        self.engine.on_hide_candidates = lambda: self.hide_candidates_signal.emit()

        self.rule_triggered_signal.connect(self._on_rule_triggered)
        self.status_changed_signal.connect(self._update_status_ui)
        self.show_candidates_signal.connect(self._on_show_candidates)
        self.hide_candidates_signal.connect(self._on_hide_candidates)

        self._setup_ui()
        self._apply_theme(self.config_mgr.config.get("theme", "dark"))
        self._refresh_categories()
        self._refresh_table()
        self._update_metrics()
        self._update_status_ui(self.engine.is_enabled)

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = (geo.height() - self.height()) // 2
            self.move(max(0, x), max(0, y))

    def show_and_activate(self):
        """Forces the window to be restored, shown, and brought to the foreground."""
        self.showNormal()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.raise_()
        self.activateWindow()

        try:
            import win32gui
            import win32con
            hwnd = int(self.winId())
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetWindowPos(
                hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            )
            win32gui.SetWindowPos(
                hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            )
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Header Bar
        header = QFrame()
        header.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        title_box = QHBoxLayout()
        lbl_icon = QLabel("⚡")
        lbl_icon.setStyleSheet("font-size: 22px;")
        lbl_title = QLabel("Quick Expander 全局文本补全")
        lbl_title.setObjectName("appTitle")
        title_box.addWidget(lbl_icon)
        title_box.addWidget(lbl_title)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        self.lbl_status_badge = QLabel("● 运行中")
        self.lbl_status_badge.setObjectName("statusBadgeActive")
        header_layout.addWidget(self.lbl_status_badge)

        self.btn_toggle_active = QPushButton("暂停全局补全")
        self.btn_toggle_active.clicked.connect(self._toggle_engine)
        header_layout.addWidget(self.btn_toggle_active)

        root_layout.addWidget(header)

        # 2. Main Content Body
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(16, 14, 16, 14)
        body_layout.setSpacing(12)

        # Metrics cards row
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(12)

        self.card_total = self._create_metric_card("总规则数", "0")
        self.card_active = self._create_metric_card("已启用规则", "0")
        self.card_categories = self._create_metric_card("规则分类数", "0")
        self.card_expansions = self._create_metric_card("累计触发次数", "0")

        metrics_layout.addWidget(self.card_total)
        metrics_layout.addWidget(self.card_active)
        metrics_layout.addWidget(self.card_categories)
        metrics_layout.addWidget(self.card_expansions)
        body_layout.addLayout(metrics_layout)

        # Tabs Container
        self.tabs = QTabWidget()

        # Tab 1: Rules Manager (with Category Sidebar)
        tab_rules = QWidget()
        rules_tab_layout = QVBoxLayout(tab_rules)
        rules_tab_layout.setContentsMargins(6, 10, 6, 6)
        rules_tab_layout.setSpacing(8)

        # Splitter between Category Sidebar and Rules Table Area
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Left: Category Sidebar ---
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("categorySidebar")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(4, 6, 4, 6)
        sidebar_layout.setSpacing(6)

        lbl_cat_title = QLabel("📂 规则分类")
        lbl_cat_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #89b4fa; padding-left: 6px;")
        sidebar_layout.addWidget(lbl_cat_title)

        self.list_categories = QListWidget()
        self.list_categories.setObjectName("categoryList")
        self.list_categories.itemClicked.connect(self._on_category_selected)
        self.list_categories.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_categories.customContextMenuRequested.connect(self._show_category_context_menu)
        sidebar_layout.addWidget(self.list_categories)

        btn_add_cat = QPushButton("➕ 新建分类")
        btn_add_cat.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        btn_add_cat.clicked.connect(self._add_new_category)
        sidebar_layout.addWidget(btn_add_cat)

        splitter.addWidget(sidebar_frame)

        # --- Right: Rules Table Area ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(8)

        # Toolbar
        toolbar = QHBoxLayout()
        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText("🔍 快速搜索触发词、说明、分类或替换内容...")
        self.edit_search.textChanged.connect(self._refresh_table)
        toolbar.addWidget(self.edit_search)

        btn_add = QPushButton("➕ 新增规则")
        btn_add.setObjectName("btnPrimary")
        btn_add.clicked.connect(self._open_add_dialog)
        toolbar.addWidget(btn_add)

        btn_refresh = QPushButton("🔄 刷新")
        btn_refresh.clicked.connect(self._on_refresh_clicked)
        toolbar.addWidget(btn_refresh)

        right_layout.addLayout(toolbar)

        # Rules Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["启用", "触发词", "替换内容", "分类", "说明", "模式", "次数", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 48)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_table_double_clicked)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        right_layout.addWidget(self.table)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        rules_tab_layout.addWidget(splitter)

        # Interactive Sandbox Section
        sandbox_frame = QFrame()
        sandbox_frame.setObjectName("sandboxFrame")
        sb_layout = QVBoxLayout(sandbox_frame)
        sb_layout.setContentsMargins(10, 8, 10, 8)
        sb_layout.setSpacing(6)

        sb_header = QHBoxLayout()
        lbl_sb_title = QLabel("🧪 实时测试沙盒 (在此处输入 411、@@em、//now 测试单项/多候选项扩展):")
        lbl_sb_title.setStyleSheet("font-weight: bold; color: #89b4fa;")
        sb_header.addWidget(lbl_sb_title)
        
        btn_clear_sb = QPushButton("清空沙盒")
        btn_clear_sb.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        btn_clear_sb.clicked.connect(lambda: self.edit_sandbox.clear())
        sb_header.addWidget(btn_clear_sb)
        sb_layout.addLayout(sb_header)

        self.edit_sandbox = QLineEdit()
        self.edit_sandbox.setPlaceholderText("试着在此处键入 411 并回车/继续打字...")
        self.edit_sandbox.setStyleSheet("font-size: 14px; padding: 8px;")
        sb_layout.addWidget(self.edit_sandbox)

        rules_tab_layout.addWidget(sandbox_frame)

        self.tabs.addTab(tab_rules, "📋 规则管理")

        # Tab 2: Settings
        self.tab_settings = SettingsTab(self.config_mgr, self.engine)
        self.tab_settings.theme_changed.connect(self._apply_theme)
        self.tab_settings.data_reloaded.connect(self._on_data_reloaded)
        self.tabs.addTab(self.tab_settings, "⚙️ 系统设置")

        # Tab 3: Guide
        tab_guide = self._create_guide_tab()
        self.tabs.addTab(tab_guide, "💡 使用指南")

        body_layout.addWidget(self.tabs)
        root_layout.addWidget(body_widget)

    def _create_metric_card(self, label: str, val: str) -> QFrame:
        card = QFrame()
        card.setProperty("class", "metricCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        
        lbl_v = QLabel(val)
        lbl_v.setProperty("class", "metricValue")
        lbl_t = QLabel(label)
        lbl_t.setProperty("class", "metricLabel")
        
        layout.addWidget(lbl_v)
        layout.addWidget(lbl_t)
        card.value_label = lbl_v
        return card

    def _create_guide_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        txt = (
            "<h2>⚡ Quick Expander 使用说明</h2>"
            "<p><b>Quick Expander</b> 是一款系统全局文本扩展工具，能够在 Windows 的<b>任何输入环境</b>中自动捕获触发词并扩展为指定文本。</p>"
            "<hr style='border: 1px solid #313244;'/>"
            "<h3>🚀 核心功能：</h3>"
            "<ul>"
            "<li><b>快速编号补全</b>：输入 <code>411</code> 自动扩展为 <code>4113293000</code>。</li>"
            "<li><b>多候选悬浮窗 (Feature 5)</b>：当同一个触发词（如 <code>411</code>）设置了多条规则时，光标旁自动弹出半透明悬浮选单，按 <code>1~9</code> 瞬间选中上屏！</li>"
            "<li><b>规则分类管理 (Feature 6)</b>：支持按【快捷编码】、【个人信息】、【工作模版】、【动态宏】进行归类与筛选。</li>"
            "<li><b>动态日期时间</b>：输入 <code>//date</code> 自动替换为今日日期；输入 <code>//now</code> 自动补全为时间与星期。</li>"
            "</ul>"
            "<h3>💡 快捷键与托盘提示：</h3>"
            "<ul>"
            "<li><b>全局暂停/恢复</b>：默认热键 <code>Ctrl+Alt+S</code>，可在设置中自由更改。</li>"
            "<li><b>后台静默运行</b>：关闭窗口时会自动最小化到系统右下角托盘。</li>"
            "<li><b>开机自启</b>：在【系统设置】中勾选“开机自动启动”，开机即可使用。</li>"
            "</ul>"
        )
        lbl = QLabel(txt)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("line-height: 150%; font-size: 13px;")
        layout.addWidget(lbl)
        layout.addStretch()
        return widget

    def _apply_theme(self, theme: str):
        if theme == "light":
            self.setStyleSheet(LIGHT_THEME)
        else:
            self.setStyleSheet(DARK_THEME)

    # --- Category Management ---
    def _refresh_categories(self):
        self.list_categories.clear()
        
        # 1. Total category item
        total_count = len(self.config_mgr.snippets)
        item_all = QListWidgetItem(f"🏷️ 全部  ({total_count})")
        item_all.setData(Qt.ItemDataRole.UserRole, "全部")
        self.list_categories.addItem(item_all)

        # 2. Categories from config
        cats = self.config_mgr.get_categories()
        category_counts = {}
        for s in self.config_mgr.snippets:
            c = s.get("category", "快捷编码")
            category_counts[c] = category_counts.get(c, 0) + 1

        cat_icons = {
            "快捷编码": "🔢",
            "个人信息": "👤",
            "工作模版": "💼",
            "动态宏": "⏰",
        }

        for cat in cats:
            count = category_counts.get(cat, 0)
            icon = cat_icons.get(cat, "📁")
            item = QListWidgetItem(f"{icon} {cat}  ({count})")
            item.setData(Qt.ItemDataRole.UserRole, cat)
            self.list_categories.addItem(item)

        # Select current active category
        for i in range(self.list_categories.count()):
            it = self.list_categories.item(i)
            if it.data(Qt.ItemDataRole.UserRole) == self.current_category:
                self.list_categories.setCurrentItem(it)
                break
        else:
            self.list_categories.setCurrentRow(0)
            self.current_category = "全部"

    def _on_category_selected(self, item):
        cat = item.data(Qt.ItemDataRole.UserRole)
        if cat:
            self.current_category = cat
            self._refresh_table()

    def _add_new_category(self):
        name, ok = QInputDialog.getText(self, "新建分类", "请输入新分类名称:")
        if ok and name.strip():
            name = name.strip()
            success = self.config_mgr.add_category(name)
            if success:
                self.current_category = name
                self._refresh_categories()
                self._refresh_table()
            else:
                QMessageBox.warning(self, "提示", "该分类名称已存在！")

    def _show_category_context_menu(self, pos):
        item = self.list_categories.itemAt(pos)
        if not item:
            return
        cat_name = item.data(Qt.ItemDataRole.UserRole)
        if not cat_name or cat_name == "全部":
            return

        menu = QMenu(self)
        act_rename = menu.addAction("✏️ 重命名分类")
        act_delete = menu.addAction("🗑️ 删除分类")

        action = menu.exec(self.list_categories.viewport().mapToGlobal(pos))
        if action == act_rename:
            new_name, ok = QInputDialog.getText(self, "重命名分类", f"重命名分类「{cat_name}」为:", text=cat_name)
            if ok and new_name.strip() and new_name.strip() != cat_name:
                self.config_mgr.rename_category(cat_name, new_name.strip())
                if self.current_category == cat_name:
                    self.current_category = new_name.strip()
                self._refresh_categories()
                self._refresh_table()
        elif action == act_delete:
            res = QMessageBox.question(
                self, "确认删除分类",
                f"确定要删除分类「{cat_name}」吗？\n该分类下的规则将自动归入其他分类，不会被删除。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if res == QMessageBox.StandardButton.Yes:
                self.config_mgr.delete_category(cat_name)
                self.current_category = "全部"
                self._refresh_categories()
                self._refresh_table()

    # --- Rules Table Management ---
    def _refresh_table(self):
        query = self.edit_search.text().lower().strip()
        snippets = self.config_mgr.snippets

        filtered = []
        for s in snippets:
            # 1. Category Filter
            if self.current_category != "全部":
                if s.get("category", "快捷编码") != self.current_category:
                    continue

            # 2. Search Query Filter
            if query:
                in_trig = query in s.get("trigger", "").lower()
                in_desc = query in s.get("description", "").lower()
                in_repl = query in s.get("replacement", "").lower()
                in_cat = query in s.get("category", "").lower()
                if not (in_trig or in_desc or in_repl or in_cat):
                    continue

            filtered.append(s)

        self.table.setRowCount(len(filtered))
        for row_idx, s in enumerate(filtered):
            # Column 0: Enabled Checkbox
            chk = QCheckBox()
            chk.setChecked(s.get("enabled", True))
            chk.toggled.connect(lambda checked, r_id=s["id"]: self._on_rule_toggle(r_id, checked))
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.addWidget(chk)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row_idx, 0, chk_widget)

            # Column 1: Trigger
            item_trig = QTableWidgetItem(s.get("trigger", ""))
            item_trig.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
            item_trig.setForeground(QColor("#89b4fa"))
            self.table.setItem(row_idx, 1, item_trig)

            # Column 2: Replacement preview
            repl = s.get("replacement", "").replace("\n", " ↵ ")
            if len(repl) > 40:
                repl = repl[:38] + "..."
            item_repl = QTableWidgetItem(repl)
            self.table.setItem(row_idx, 2, item_repl)

            # Column 3: Category
            item_cat = QTableWidgetItem(s.get("category", "快捷编码"))
            item_cat.setForeground(QColor("#b4befe"))
            self.table.setItem(row_idx, 3, item_cat)

            # Column 4: Description
            item_desc = QTableWidgetItem(s.get("description", ""))
            self.table.setItem(row_idx, 4, item_desc)

            # Column 5: Mode
            mode_text = "⚡ 即时" if s.get("mode") == "instant" else "⌨️ 触发键"
            item_mode = QTableWidgetItem(mode_text)
            self.table.setItem(row_idx, 5, item_mode)

            # Column 6: Count
            item_count = QTableWidgetItem(str(s.get("use_count", 0)))
            item_count.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 6, item_count)

            # Column 7: Action Buttons
            btn_box = QWidget()
            b_layout = QHBoxLayout(btn_box)
            b_layout.setContentsMargins(2, 2, 2, 2)
            b_layout.setSpacing(4)

            btn_edit = QPushButton("编辑")
            btn_edit.setStyleSheet("padding: 2px 8px; font-size: 11px;")
            btn_edit.clicked.connect(lambda _, r_id=s["id"]: self._open_edit_dialog(r_id))

            btn_del = QPushButton("删除")
            btn_del.setObjectName("btnDanger")
            btn_del.setStyleSheet("padding: 2px 8px; font-size: 11px;")
            btn_del.clicked.connect(lambda _, r_id=s["id"]: self._delete_rule(r_id))

            b_layout.addWidget(btn_edit)
            b_layout.addWidget(btn_del)
            self.table.setCellWidget(row_idx, 7, btn_box)

            # Associate data ID with row
            item_trig.setData(Qt.ItemDataRole.UserRole, s["id"])

        self._update_metrics()

    def _update_metrics(self):
        total = len(self.config_mgr.snippets)
        active = len(self.config_mgr.get_enabled_snippets())
        categories_count = len(self.config_mgr.get_categories())
        expansions = sum(s.get("use_count", 0) for s in self.config_mgr.snippets)

        self.card_total.value_label.setText(str(total))
        self.card_active.value_label.setText(str(active))
        self.card_categories.value_label.setText(str(categories_count))
        self.card_expansions.value_label.setText(str(expansions))

    def _on_rule_toggle(self, rule_id: str, checked: bool):
        self.config_mgr.update_snippet(rule_id, enabled=checked)
        self._update_metrics()

    def _open_add_dialog(self):
        cats = self.config_mgr.get_categories()
        dialog = RuleDialog(self, categories=cats)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                self.config_mgr.add_snippet(
                    trigger=data["trigger"],
                    replacement=data["replacement"],
                    description=data["description"],
                    category=data.get("category", "快捷编码"),
                    match_case=data["match_case"],
                    mode=data["mode"],
                    method=data["method"]
                )
                self._refresh_categories()
                self._refresh_table()

    def _open_edit_dialog(self, rule_id: str):
        rule = next((s for s in self.config_mgr.snippets if s["id"] == rule_id), None)
        if not rule:
            return
        cats = self.config_mgr.get_categories()
        dialog = RuleDialog(self, rule_data=rule, categories=cats)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                self.config_mgr.update_snippet(rule_id, **data)
                self._refresh_categories()
                self._refresh_table()

    def _delete_rule(self, rule_id: str):
        rule = next((s for s in self.config_mgr.snippets if s["id"] == rule_id), None)
        if not rule:
            return
        trig = rule.get("trigger", "")
        res = QMessageBox.question(
            self, "确认删除", f"确定要删除触发词为 <b>{trig}</b> 的规则吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            self.config_mgr.delete_snippet(rule_id)
            self._refresh_categories()
            self._refresh_table()

    def _on_table_double_clicked(self, index):
        row = index.row()
        item = self.table.item(row, 1)
        if item:
            rule_id = item.data(Qt.ItemDataRole.UserRole)
            if rule_id:
                self._open_edit_dialog(rule_id)

    def _show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return
        row = item.row()
        trig_item = self.table.item(row, 1)
        if not trig_item:
            return
        rule_id = trig_item.data(Qt.ItemDataRole.UserRole)
        rule = next((s for s in self.config_mgr.snippets if s["id"] == rule_id), None)
        if not rule:
            return

        menu = QMenu(self)
        act_edit = menu.addAction("✏️ 编辑规则")
        act_toggle = menu.addAction("⏸ 禁用规则" if rule.get("enabled", True) else "▶ 启用规则")
        menu.addSeparator()
        act_del = menu.addAction("🗑️ 删除规则")

        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == act_edit:
            self._open_edit_dialog(rule_id)
        elif action == act_toggle:
            self.config_mgr.toggle_snippet(rule_id)
            self._refresh_table()
        elif action == act_del:
            self._delete_rule(rule_id)

    def _on_refresh_clicked(self):
        self._refresh_categories()
        self._refresh_table()

    def _toggle_engine(self):
        self.engine.toggle_enabled()

    def _update_status_ui(self, is_enabled: bool):
        if is_enabled:
            self.lbl_status_badge.setText("● 运行中")
            self.lbl_status_badge.setObjectName("statusBadgeActive")
            self.btn_toggle_active.setText("暂停全局补全")
        else:
            self.lbl_status_badge.setText("⏸ 已暂停")
            self.lbl_status_badge.setObjectName("statusBadgePaused")
            self.btn_toggle_active.setText("恢复全局补全")
        
        self.lbl_status_badge.style().unpolish(self.lbl_status_badge)
        self.lbl_status_badge.style().polish(self.lbl_status_badge)

    def _on_rule_triggered(self, snippet: dict, resolved_text: str):
        self._refresh_categories()
        self._refresh_table()

    def _on_data_reloaded(self):
        self._refresh_categories()
        self._refresh_table()

    # --- Candidate Popup Slots ---
    def _on_show_candidates(self, candidates: list, trigger: str):
        self.candidate_popup.show_candidates(candidates, trigger)

    def _on_hide_candidates(self):
        self.candidate_popup.hide_popup()

    def closeEvent(self, event):
        """Intercepts window close and minimizes to system tray instead."""
        event.ignore()
        self.hide()
