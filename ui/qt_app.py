
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QDir, QFileSystemWatcher

from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPlainTextEdit, QTreeView, QFileSystemModel,
    QTabWidget, QLabel, QPushButton, QToolBar, QFileDialog,
    QMessageBox, QInputDialog, QStatusBar, QFrame
)

from core.engine import PolyCodeEngine


APP_NAME = "PolyCode IDE"
VERSION = "0.0.2"

BG = "#111714"
PANEL = "#18211C"
PANEL_ALT = "#202B24"
EDITOR_BG = "#101512"
BORDER = "#2C3A30"
GREEN = "#8BEA9D"
GREEN_DARK = "#3FBA68"
TEXT = "#DCE7DE"
MUTED = "#819487"
BLUE = "#75BFFF"
ORANGE = "#E7B879"
RED = "#FF7777"


class PolyHighlighter(QSyntaxHighlighter):
    """Lightweight syntax highlighting for mixed-language .poly files."""

    def __init__(self, document):
        super().__init__(document)
        self.language = None
        self.rules = []

        self.marker_format = self.make_format("#8BEA9D", True)
        self.keyword_format = self.make_format("#C792EA", True)
        self.string_format = self.make_format("#E7B879")
        self.number_format = self.make_format("#F78C6C")
        self.comment_format = self.make_format("#718578", italic=True)
        self.function_format = self.make_format("#82AAFF")
        self.type_format = self.make_format("#FFCB6B")

    @staticmethod
    def make_format(color, bold=False, italic=False):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def highlightBlock(self, text):
        stripped = text.strip()

        markers = {
            "@python": "python",
            "@cpp": "cpp",
            "@javascript": "javascript",
        }

        if stripped in markers:
            self.language = markers[stripped]
            self.setFormat(0, len(text), self.marker_format)
            return

        if not self.language:
            return

        import re

        rules = [
            (r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', self.string_format),
            (r"\b\d+(?:\.\d+)?\b", self.number_format),
            (r"\b(?:True|False|None|and|or|not|if|else|elif|for|while|"
             r"def|class|return|import|from|as|in|is|pass|break|continue|"
             r"try|except|finally|with|lambda|yield|async|await|"
             r"const|let|var|function|new|this|typeof|true|false|null|"
             r"int|float|double|char|bool|void|long|short|auto|"
             r"public|private|protected|static|return|using|namespace)\b",
             self.keyword_format),
            (r"\b[A-Za-z_]\w*(?=\s*\()", self.function_format),
            (r"//.*|#.*", self.comment_format),
        ]

        for pattern, fmt in rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(self.editor.line_number_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFont(QFont("Consolas", 11))
        self.setTabStopDistance(
            self.fontMetrics().horizontalAdvance(" ") * 4
        )
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setStyleSheet("""
            QPlainTextEdit {
                background: #101512;
                color: #DCE7DE;
                border: none;
                padding: 8px 12px 8px 4px;
                selection-background-color: #294D35;
            }
        """)

        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.highlighter = PolyHighlighter(self.document())

        self.update_line_number_width()
        self.highlight_current_line()

    def line_number_width(self):
        digits = max(2, len(str(max(1, self.blockCount()))))
        return 14 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_line_number_width(self, *_):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(),
                self.line_number_area.width(),
                rect.height(),
            )

        if rect.contains(self.viewport().rect()):
            self.update_line_number_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = self.contentsRect()
        self.line_number_area.setGeometry(
            rect.left(),
            rect.top(),
            self.line_number_width(),
            rect.height(),
        )

    def paint_line_numbers(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#151D18"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block)
            .translated(self.contentOffset())
            .top()
        )
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                color = (
                    QColor("#8BEA9D")
                    if block_number == self.textCursor().blockNumber()
                    else QColor("#65776A")
                )
                painter.setPen(color)
                painter.drawText(
                    0, top, self.line_number_area.width() - 7,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_number + 1),
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        from PySide6.QtGui import ExtraSelection

        selections = []
        if not self.isReadOnly():
            selection = ExtraSelection()
            selection.format.setBackground(QColor("#18241C"))
            selection.format.setProperty(
                QTextCharFormat.Property.FullWidthSelection, True
            )
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selections.append(selection)

        self.setExtraSelections(selections)
        self.line_number_area.update()


class PolyCodeIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} • v{VERSION}")
        self.resize(1400, 850)
        self.setMinimumSize(950, 600)

        self.engine = PolyCodeEngine()
        self.workspace = Path.home() / "PolyCodeProjects"
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.file_editors = {}
        self.file_paths = {}

        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {BG};
                color: {TEXT};
            }}
            QMenuBar {{
                background: {PANEL};
                color: {TEXT};
                padding: 5px;
            }}
            QMenuBar::item:selected, QMenu::item:selected {{
                background: {PANEL_ALT};
                color: {GREEN};
            }}
            QMenu {{
                background: {PANEL};
                color: {TEXT};
                border: 1px solid {BORDER};
            }}
            QToolBar {{
                background: {PANEL};
                border: none;
                spacing: 8px;
                padding: 8px;
            }}
            QPushButton {{
                background: {GREEN_DARK};
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 9px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {GREEN};
                color: {BG};
            }}
            QTabWidget::pane {{
                border: 1px solid {BORDER};
                top: -1px;
            }}
            QTabBar::tab {{
                background: {PANEL};
                color: {MUTED};
                padding: 10px 16px;
                border-right: 1px solid {BORDER};
            }}
            QTabBar::tab:selected {{
                background: {EDITOR_BG};
                color: {GREEN};
                border-top: 2px solid {GREEN_DARK};
            }}
            QTreeView {{
                background: {PANEL};
                color: {TEXT};
                border: none;
                outline: none;
                padding: 5px;
            }}
            QTreeView::item {{
                height: 27px;
            }}
            QTreeView::item:selected {{
                background: #294D35;
                color: {GREEN};
            }}
            QSplitter::handle {{
                background: {BORDER};
            }}
            QSplitter::handle:hover {{
                background: {GREEN_DARK};
            }}
            QStatusBar {{
                background: {GREEN_DARK};
                color: #FFFFFF;
            }}
        """)

        self.build_menu()
        self.build_ui()
        self.refresh_workspace()

    def build_menu(self):
        menu = self.menuBar()

        file_menu = menu.addMenu("File")
        self.add_action(file_menu, "New PolyCode File", self.new_file,
                        "Ctrl+N")
        self.add_action(file_menu, "New Folder", self.new_folder)
        self.add_action(file_menu, "Open File", self.open_file, "Ctrl+O")
        self.add_action(file_menu, "Open Workspace", self.open_workspace)
        self.add_action(file_menu, "Save", self.save_current, "Ctrl+S")
        file_menu.addSeparator()
        self.add_action(file_menu, "Exit", self.close)

        run_menu = menu.addMenu("Run")
        self.add_action(run_menu, "Run Current File", self.run_current,
                        "F5")
        self.add_action(run_menu, "Clear Output", self.clear_output)

        help_menu = menu.addMenu("Help")
        self.add_action(
            help_menu, "About PolyCode",
            lambda: QMessageBox.about(
                self, "About PolyCode",
                f"{APP_NAME} {VERSION}<br>"
                "One file. Multiple languages. One execution flow."
            )
        )

    @staticmethod
    def add_action(menu, label, callback, shortcut=None):
        action = QAction(label, menu)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(callback)
        menu.addAction(action)
        return action

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        brand = QLabel("  P  POLYCODE")
        brand.setStyleSheet(
            f"color: {GREEN}; font-size: 18px; font-weight: bold;"
            "padding: 5px 12px;"
        )
        toolbar.addWidget(brand)

        subtitle = QLabel("MULTI-LANGUAGE DEVELOPMENT")
        subtitle.setStyleSheet(
            f"color: {MUTED}; font-size: 10px; padding-left: 10px;"
        )
        toolbar.addWidget(subtitle)

        spacer = QWidget()
        spacer.setSizePolicy(
            spacer.sizePolicy().Policy.Expanding,
            spacer.sizePolicy().Policy.Preferred
        )
        toolbar.addWidget(spacer)

        run_button = QPushButton("▶  RUN")
        run_button.clicked.connect(self.run_current)
        toolbar.addWidget(run_button)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)
        root.addWidget(split, 1)

        # Workspace explorer
        explorer = QWidget()
        explorer.setMinimumWidth(180)
        explorer.setMaximumWidth(480)
        explorer_layout = QVBoxLayout(explorer)
        explorer_layout.setContentsMargins(0, 0, 0, 0)
        explorer_layout.setSpacing(0)

        explorer_title = QLabel("  EXPLORER")
        explorer_title.setStyleSheet(
            f"background: {PANEL}; color: {GREEN};"
            "font-weight: bold; padding: 13px 8px;"
        )
        explorer_layout.addWidget(explorer_title)

        explorer_actions = QHBoxLayout()
        explorer_actions.setContentsMargins(8, 6, 8, 6)

        new_file_button = QPushButton("+ File")
        new_file_button.clicked.connect(self.new_file)
        new_folder_button = QPushButton("+ Folder")
        new_folder_button.clicked.connect(self.new_folder)

        explorer_actions.addWidget(new_file_button)
        explorer_actions.addWidget(new_folder_button)
        explorer_layout.addLayout(explorer_actions)

        self.fs_model = QFileSystemModel(self)
        self.fs_model.setFilter(
            QDir.Filter.AllDirs
            | QDir.Filter.Files
            | QDir.Filter.NoDotAndDotDot
        )
        self.fs_model.setRootPath(str(self.workspace))

        self.tree = QTreeView()
        self.tree.setModel(self.fs_model)
        self.tree.setRootIndex(self.fs_model.index(str(self.workspace)))
        self.tree.setHeaderHidden(True)
        for column in range(1, 4):
            self.tree.hideColumn(column)
        self.tree.doubleClicked.connect(self.on_tree_open)
        self.tree.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.tree.customContextMenuRequested.connect(
            self.explorer_context_menu
        )
        explorer_layout.addWidget(self.tree, 1)

        split.addWidget(explorer)

        # Main editor and output area
        right_split = QSplitter(Qt.Orientation.Vertical)
        right_split.setChildrenCollapsible(False)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_status)
        right_split.addWidget(self.tabs)

        output_panel = QWidget()
        output_layout = QVBoxLayout(output_panel)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(0)

        output_header = QHBoxLayout()
        output_header.setContentsMargins(10, 7, 10, 7)
        output_title = QLabel("OUTPUT")
        output_title.setStyleSheet(
            f"color: {GREEN}; font-weight: bold;"
        )
        output_header.addWidget(output_title)
        output_header.addStretch()

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_output)
        output_header.addWidget(clear_button)
        output_layout.addLayout(output_header)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 10))
        self.output.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {EDITOR_BG};
                color: {TEXT};
                border: none;
                padding: 8px;
            }}
        """)
        output_layout.addWidget(self.output)

        right_split.addWidget(output_panel)
        right_split.setSizes([570, 190])
        split.addWidget(right_split)
        split.setSizes([250, 1150])

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

        self.welcome_page()

    def welcome_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo = QLabel("P")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(
            f"background: {GREEN_DARK}; color: white;"
            "font-size: 38px; font-weight: bold;"
            "min-width: 85px; max-width: 85px;"
            "min-height: 75px; max-height: 75px;"
        )
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)

        heading = QLabel("Welcome to PolyCode")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setStyleSheet(
            f"color: {GREEN}; font-size: 28px; font-weight: bold;"
            "padding-top: 14px;"
        )
        layout.addWidget(heading)

        tagline = QLabel("One file. Multiple languages. One execution flow.")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet(
            f"color: {MUTED}; font-size: 13px; padding: 10px;"
        )
        layout.addWidget(tagline)

        create_button = QPushButton("+  Create PolyCode File")
        create_button.clicked.connect(self.new_file)
        layout.addWidget(
            create_button, alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.tabs.addTab(page, "Welcome")

    def refresh_workspace(self):
        self.fs_model.setRootPath(str(self.workspace))
        self.tree.setRootIndex(self.fs_model.index(str(self.workspace)))

    def new_file(self):
        name, ok = QInputDialog.getText(
            self, "New PolyCode File", "File name:"
        )
        if not ok or not name.strip():
            return

        name = name.strip()
        if not name.lower().endswith(".poly"):
            name += ".poly"

        parent = self.workspace
        indexes = self.tree.selectedIndexes()
        if indexes:
            selected = Path(self.fs_model.filePath(indexes[0]))
            if selected.is_dir():
                parent = selected
            elif selected.parent.is_dir():
                parent = selected.parent

        path = parent / name
        if path.exists():
            QMessageBox.warning(self, "File exists", "That file already exists.")
            return

        path.write_text(
            '@python\nprint("Hello from PolyCode!")\n\n'
            '@cpp\ncout << "Hello from C++" << endl;\n\n'
            '@javascript\nconsole.log("Hello from JavaScript");\n',
            encoding="utf-8",
        )
        self.refresh_workspace()
        self.open_poly_file(path)

    def new_folder(self):
        name, ok = QInputDialog.getText(
            self, "New Folder", "Folder name:"
        )
        if not ok or not name.strip():
            return

        parent = self.workspace
        indexes = self.tree.selectedIndexes()
        if indexes:
            selected = Path(self.fs_model.filePath(indexes[0]))
            parent = selected if selected.is_dir() else selected.parent

        path = parent / name.strip()
        try:
            path.mkdir()
        except FileExistsError:
            QMessageBox.warning(
                self, "Folder exists", "That folder already exists."
            )
        except OSError as exc:
            QMessageBox.critical(self, "Folder error", str(exc))

        self.refresh_workspace()

    def open_workspace(self):
        chosen = QFileDialog.getExistingDirectory(
            self, "Open PolyCode Workspace", str(self.workspace)
        )
        if chosen:
            self.workspace = Path(chosen)
            self.fs_model.setRootPath(str(self.workspace))
            self.tree.setRootIndex(self.fs_model.index(str(self.workspace)))
            self.statusBar().showMessage(
                f"Workspace: {self.workspace}"
            )

    def open_file(self):
        chosen, _ = QFileDialog.getOpenFileName(
            self, "Open PolyCode File", str(self.workspace),
            "PolyCode files (*.poly)"
        )
        if chosen:
            self.open_poly_file(Path(chosen))

    def on_tree_open(self, index):
        path = Path(self.fs_model.filePath(index))
        if path.is_file() and path.suffix.lower() == ".poly":
            self.open_poly_file(path)

    def open_poly_file(self, path):
        path = Path(path).resolve()
        if path.suffix.lower() != ".poly":
            QMessageBox.warning(
                self, "Unsupported file",
                "For now, PolyCode opens .poly files only."
            )
            return

        if path in self.file_editors:
            self.tabs.setCurrentWidget(self.file_editors[path])
            return

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Open error", str(exc))
            return

        editor = CodeEditor()
        editor.setPlainText(content)
        editor.document().modificationChanged.connect(
            lambda modified, p=path: self.update_tab_title(p, modified)
        )

        self.file_editors[path] = editor
        self.file_paths[editor] = path
        index = self.tabs.addTab(editor, f"P  {path.name}")
        self.tabs.setCurrentIndex(index)
        self.statusBar().showMessage(str(path))

    def update_tab_title(self, path, modified):
        editor = self.file_editors.get(path)
        if editor is None:
            return
        index = self.tabs.indexOf(editor)
        if index >= 0:
            prefix = "* " if modified else "P  "
            self.tabs.setTabText(index, prefix + path.name)

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if widget is None:
            return

        path = self.file_paths.get(widget)
        if path is None:
            self.tabs.removeTab(index)
            widget.deleteLater()
            return

        if widget.document().isModified():
            answer = QMessageBox.question(
                self, "Unsaved changes",
                f"Save changes to {path.name} before closing?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if answer == QMessageBox.StandardButton.Cancel:
                return
            if answer == QMessageBox.StandardButton.Save:
                self.save_editor(widget)
                if widget.document().isModified():
                    return

        self.tabs.removeTab(index)
        self.file_editors.pop(path, None)
        self.file_paths.pop(widget, None)
        widget.deleteLater()

    def save_editor(self, editor):
        path = self.file_paths.get(editor)
        if path is None:
            return False
        try:
            path.write_text(editor.toPlainText(), encoding="utf-8")
            editor.document().setModified(False)
            self.statusBar().showMessage(f"Saved {path.name}")
            return True
        except OSError as exc:
            QMessageBox.critical(self, "Save error", str(exc))
            return False

    def save_current(self):
        editor = self.tabs.currentWidget()
        if isinstance(editor, CodeEditor):
            self.save_editor(editor)

    def run_current(self):
        editor = self.tabs.currentWidget()
        if not isinstance(editor, CodeEditor):
            self.output.setPlainText("Open a .poly file before running.")
            return

        self.save_current()
        source = editor.toPlainText()
        self.output.setPlainText("Running PolyCode...\n")
        QApplication.processEvents()

        try:
            result = self.engine.run(source)
            self.output.setPlainText(result or "Program completed with no output.")
            self.statusBar().showMessage("Execution finished")
        except Exception as exc:
            self.output.setPlainText(f"PolyCode internal error:\n{exc}")
            self.statusBar().showMessage("Execution failed")

    def clear_output(self):
        self.output.clear()

    def explorer_context_menu(self, position):
        index = self.tree.indexAt(position)
        if not index.isValid():
            return

        path = Path(self.fs_model.filePath(index))
        from PySide6.QtWidgets import QMenu

        menu = QMenu(self)
        open_action = menu.addAction("Open")
        new_file_action = menu.addAction("New PolyCode File")
        new_folder_action = menu.addAction("New Folder")
        menu.addSeparator()
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")

        chosen = menu.exec(self.tree.viewport().mapToGlobal(position))

        if chosen == open_action:
            if path.is_dir():
                self.tree.setExpanded(index, not self.tree.isExpanded(index))
            elif path.suffix.lower() == ".poly":
                self.open_poly_file(path)
        elif chosen == new_file_action:
            self.new_file()
        elif chosen == new_folder_action:
            self.new_folder()
        elif chosen == rename_action:
            new_name, ok = QInputDialog.getText(
                self, "Rename", "New name:", text=path.name
            )
            if ok and new_name.strip():
                target = path.with_name(new_name.strip())
                try:
                    path.rename(target)
                    if path in self.file_editors:
                        editor = self.file_editors.pop(path)
                        self.file_paths[editor] = target
                        self.file_editors[target] = editor
                    self.refresh_workspace()
                except OSError as exc:
                    QMessageBox.critical(self, "Rename error", str(exc))
        elif chosen == delete_action:
            answer = QMessageBox.question(
                self, "Delete",
                f"Delete '{path.name}'?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.Yes:
                try:
                    if path.is_dir():
                        import shutil
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    self.refresh_workspace()
                except OSError as exc:
                    QMessageBox.critical(self, "Delete error", str(exc))

    def update_status(self, *_):
        editor = self.tabs.currentWidget()
        if isinstance(editor, CodeEditor):
            cursor = editor.textCursor()
            self.statusBar().showMessage(
                f"Ln {cursor.blockNumber() + 1}, "
                f"Col {cursor.positionInBlock() + 1}  |  "
                f"{self.workspace}"
            )

    def closeEvent(self, event):
        for editor in list(self.file_paths):
            if editor.document().isModified():
                answer = QMessageBox.question(
                    self, "Unsaved changes",
                    "There are unsaved changes. Save before exiting?",
                    QMessageBox.StandardButton.Save
                    | QMessageBox.StandardButton.Discard
                    | QMessageBox.StandardButton.Cancel,
                )
                if answer == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return
                if answer == QMessageBox.StandardButton.Save:
                    if not self.save_editor(editor):
                        event.ignore()
                        return
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    window = PolyCodeIDE()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
