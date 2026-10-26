"""
UI Styling and Themes for Quick Expander
Provides polished dark and light themes with Fluent / Modern design aesthetics,
including Category Sidebar, Badges, and Candidate Popup styling.
"""

DARK_THEME = """
QWidget {
    background-color: #181825;
    color: #cdd6f4;
    font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 13px;
}

/* Header & Top Bar */
QFrame#headerFrame {
    background-color: #1e1e2e;
    border-bottom: 1px solid #313244;
    padding: 12px 16px;
}

QLabel#appTitle {
    font-size: 18px;
    font-weight: bold;
    color: #cdd6f4;
}

QLabel#statusBadgeActive {
    background-color: rgba(166, 227, 161, 0.15);
    color: #a6e3a1;
    border: 1px solid #a6e3a1;
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: bold;
    font-size: 12px;
}

QLabel#statusBadgePaused {
    background-color: rgba(249, 226, 175, 0.15);
    color: #f9e2af;
    border: 1px solid #f9e2af;
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: bold;
    font-size: 12px;
}

/* Stats Card */
QFrame.metricCard {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 10px 14px;
}

QLabel.metricValue {
    font-size: 20px;
    font-weight: bold;
    color: #89b4fa;
}

QLabel.metricLabel {
    font-size: 11px;
    color: #a6adc8;
}

/* Category Sidebar */
QFrame#categorySidebar {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 6px;
}

QListWidget#categoryList {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget#categoryList::item {
    padding: 8px 12px;
    border-radius: 6px;
    margin-bottom: 3px;
    color: #cdd6f4;
}

QListWidget#categoryList::item:hover {
    background-color: #313244;
}

QListWidget#categoryList::item:selected {
    background-color: #89b4fa;
    color: #11111b;
    font-weight: bold;
}

/* Search and Inputs */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #585b70;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #89b4fa;
    background-color: #181825;
}

/* Buttons */
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #45475a;
    border-color: #585b70;
}

QPushButton:pressed {
    background-color: #585b70;
}

QPushButton#btnPrimary {
    background-color: #89b4fa;
    color: #11111b;
    border: none;
    font-weight: bold;
}

QPushButton#btnPrimary:hover {
    background-color: #b4befe;
}

QPushButton#btnPrimary:pressed {
    background-color: #74c7ec;
}

QPushButton#btnSuccess {
    background-color: #a6e3a1;
    color: #11111b;
    border: none;
    font-weight: bold;
}

QPushButton#btnSuccess:hover {
    background-color: #94e2d5;
}

QPushButton#btnDanger {
    background-color: rgba(243, 139, 168, 0.15);
    color: #f38ba8;
    border: 1px solid #f38ba8;
}

QPushButton#btnDanger:hover {
    background-color: #f38ba8;
    color: #11111b;
}

/* Table View */
QTableWidget {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 8px;
    gridline-color: #313244;
    selection-background-color: #313244;
    selection-color: #cdd6f4;
}

QTableWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #28293d;
}

QTableWidget::item:selected {
    background-color: #313244;
}

QHeaderView::section {
    background-color: #181825;
    color: #a6adc8;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #313244;
    font-weight: bold;
    font-size: 12px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #313244;
    background-color: #1e1e2e;
    border-radius: 8px;
    margin-top: -1px;
}

QTabBar::tab {
    background-color: #181825;
    color: #a6adc8;
    padding: 8px 18px;
    border: 1px solid #313244;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background-color: #1e1e2e;
    color: #89b4fa;
    font-weight: bold;
    border-bottom: 1px solid #1e1e2e;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background-color: #181825;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #45475a;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* CheckBox */
QCheckBox {
    spacing: 8px;
    color: #cdd6f4;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #45475a;
    background-color: #1e1e2e;
}

QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}

/* Sandbox Box */
QFrame#sandboxFrame {
    background-color: #1e1e2e;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 10px;
}
"""

LIGHT_THEME = """
QWidget {
    background-color: #f8fafc;
    color: #1e293b;
    font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 13px;
}

QFrame#headerFrame {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 12px 16px;
}

QLabel#appTitle {
    font-size: 18px;
    font-weight: bold;
    color: #0f172a;
}

QLabel#statusBadgeActive {
    background-color: #ecfdf5;
    color: #059669;
    border: 1px solid #10b981;
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: bold;
    font-size: 12px;
}

QLabel#statusBadgePaused {
    background-color: #fffbeb;
    color: #d97706;
    border: 1px solid #f59e0b;
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: bold;
    font-size: 12px;
}

QFrame.metricCard {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 14px;
}

QLabel.metricValue {
    font-size: 20px;
    font-weight: bold;
    color: #2563eb;
}

QLabel.metricLabel {
    font-size: 11px;
    color: #64748b;
}

/* Category Sidebar */
QFrame#categorySidebar {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 6px;
}

QListWidget#categoryList {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget#categoryList::item {
    padding: 8px 12px;
    border-radius: 6px;
    margin-bottom: 3px;
    color: #1e293b;
}

QListWidget#categoryList::item:hover {
    background-color: #f1f5f9;
}

QListWidget#categoryList::item:selected {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: bold;
}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #2563eb;
    background-color: #ffffff;
}

QPushButton {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #f1f5f9;
    border-color: #94a3b8;
}

QPushButton#btnPrimary {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    font-weight: bold;
}

QPushButton#btnPrimary:hover {
    background-color: #1d4ed8;
}

QPushButton#btnSuccess {
    background-color: #10b981;
    color: #ffffff;
    border: none;
    font-weight: bold;
}

QPushButton#btnDanger {
    background-color: #fef2f2;
    color: #dc2626;
    border: 1px solid #ef4444;
}

QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #f1f5f9;
}

QTableWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #f1f5f9;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #475569;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    font-weight: bold;
    font-size: 12px;
}

QTabWidget::pane {
    border: 1px solid #e2e8f0;
    background-color: #ffffff;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #f8fafc;
    color: #64748b;
    padding: 8px 18px;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #2563eb;
    font-weight: bold;
}

QFrame#sandboxFrame {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 10px;
}
"""
