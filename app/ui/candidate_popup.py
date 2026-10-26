"""
Candidate Popup Window
Displays an elegant, unobtrusive floating candidate list near the mouse/typing cursor
when a trigger matches multiple snippets.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QCursor, QFont, QColor


class CandidateItemWidget(QFrame):
    clicked = pyqtSignal(int)

    def __init__(self, index: int, snippet: dict, parent=None):
        super().__init__(parent)
        self.index = index
        self.snippet = snippet
        self.setObjectName("candidateItem")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # 1. Number Badge
        lbl_num = QLabel(f"[{index + 1}]")
        lbl_num.setStyleSheet("font-weight: bold; color: #89b4fa; font-family: monospace; font-size: 12px;")
        layout.addWidget(lbl_num)

        # 2. Replacement Preview
        repl = snippet.get("replacement", "").replace("\n", " ↵ ")
        if len(repl) > 28:
            repl = repl[:26] + "..."
        lbl_repl = QLabel(repl)
        lbl_repl.setStyleSheet("font-weight: bold; color: #cdd6f4; font-size: 12px;")
        layout.addWidget(lbl_repl)

        # 3. Description
        desc = snippet.get("description", "")
        if desc:
            if len(desc) > 16:
                desc = desc[:14] + "..."
            lbl_desc = QLabel(f"({desc})")
            lbl_desc.setStyleSheet("color: #a6adc8; font-size: 11px;")
            layout.addWidget(lbl_desc)

        layout.addStretch()

        # 4. Category Tag
        cat = snippet.get("category", "")
        if cat:
            lbl_cat = QLabel(cat)
            lbl_cat.setStyleSheet(
                "background-color: #313244; color: #b4befe; border-radius: 4px; padding: 1px 5px; font-size: 10px;"
            )
            layout.addWidget(lbl_cat)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)


class CandidatePopup(QWidget):
    candidate_chosen = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.candidates: list[dict] = []
        self.trigger = ""

        # Auto-dismiss timer (12s)
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.hide_popup)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)

        self.card = QFrame(self)
        self.card.setObjectName("candidatePopupCard")
        self.card.setStyleSheet("""
            QFrame#candidatePopupCard {
                background-color: rgba(24, 24, 37, 0.95);
                border: 1px solid #45475a;
                border-radius: 10px;
                box-shadow: 0px 8px 16px rgba(0, 0, 0, 0.4);
            }
            QFrame#candidateItem {
                background-color: transparent;
                border-radius: 6px;
            }
            QFrame#candidateItem:hover {
                background-color: #313244;
            }
        """)

        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(6, 6, 6, 6)
        self.card_layout.setSpacing(2)

        main_layout.addWidget(self.card)

    def show_candidates(self, candidates: list[dict], trigger: str):
        """Displays the candidate popup with given candidates list."""
        if not candidates:
            self.hide_popup()
            return

        self.candidates = candidates[:9]  # Max 9 candidates (numbers 1-9)
        self.trigger = trigger

        # Clear previous items
        while self.card_layout.count() > 0:
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Header hint
        lbl_hint = QLabel(f"⚡ 触发词「{trigger}」有多条候选 (按 1~{len(self.candidates)} 选择):")
        lbl_hint.setStyleSheet("color: #f9e2af; font-size: 10px; font-weight: bold; padding: 2px 6px;")
        self.card_layout.addWidget(lbl_hint)

        # Add candidate item rows
        for idx, snip in enumerate(self.candidates):
            item_widget = CandidateItemWidget(idx, snip, self.card)
            item_widget.clicked.connect(self._on_item_clicked)
            self.card_layout.addWidget(item_widget)

        self.adjustSize()

        # Position near cursor
        self._position_near_cursor()
        self.show()
        self.dismiss_timer.start(12000)

    def _position_near_cursor(self):
        cursor_pos = QCursor.pos()
        target_x = cursor_pos.x() + 14
        target_y = cursor_pos.y() + 18

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            if target_x + self.width() > geo.right():
                target_x = max(geo.left(), geo.right() - self.width() - 10)
            if target_y + self.height() > geo.bottom():
                target_y = max(geo.top(), cursor_pos.y() - self.height() - 10)

        self.move(QPoint(target_x, target_y))

    def _on_item_clicked(self, index: int):
        self.select_index(index)

    def select_index(self, index: int) -> bool:
        """Selects candidate at index (0-based) and emits signal."""
        if 0 <= index < len(self.candidates):
            selected = self.candidates[index]
            self.hide_popup()
            self.candidate_chosen.emit(selected)
            return True
        return False

    def hide_popup(self):
        self.dismiss_timer.stop()
        self.hide()
        self.candidates = []
