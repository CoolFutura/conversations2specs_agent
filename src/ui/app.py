from __future__ import annotations

import os
import sys
from dataclasses import asdict
from typing import Callable, Iterable, Sequence

from dotenv import load_dotenv
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.cli.wiring import (
    build_add_decision_use_case,
    build_approve_pu_use_case,
    build_ingest_use_case,
    build_list_artifacts_use_case,
    build_list_open_questions_use_case,
    build_list_proposed_updates_use_case,
    build_transform_artifacts_use_case,
    build_transform_oq_use_case,
)


MAX_CELL_LEN = 80


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    text = str(value)
    if text.strip() == "":
        return "-"
    return text


def _truncate(value: object, limit: int = MAX_CELL_LEN) -> str:
    text = _fmt(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


class DecisionDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, decision: str = "", rationale: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Decision")

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.decision_edit = QLineEdit(decision)
        self.rationale_edit = QTextEdit()
        self.rationale_edit.setPlainText(rationale)
        self.rationale_edit.setFixedHeight(120)

        form.addRow("Decision", self.decision_edit)
        form.addRow("Rationale", self.rationale_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> tuple[str, str]:
        return self.decision_edit.text().strip(), self.rationale_edit.toPlainText().strip()


class RecordsTab(QWidget):
    def __init__(
        self,
        title: str,
        columns: Sequence[tuple[str, Callable[[object], object]]],
        load_records: Callable[[], Iterable[object]],
        format_details: Callable[[object], str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.title = title
        self.columns = list(columns)
        self.load_records = load_records
        self.format_details = format_details
        self.records: list[object] = []
        self._all_records: list[object] = []

        layout = QVBoxLayout(self)
        top_bar = QHBoxLayout()
        self.count_label = QLabel("Count: 0")
        top_bar.addWidget(self.count_label)
        top_bar.addStretch()
        top_bar.addWidget(QLabel("Filter"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Type to filter…")
        self.filter_input.textChanged.connect(self._apply_filter)
        top_bar.addWidget(self.filter_input)
        layout.addLayout(top_bar)

        splitter = QSplitter(Qt.Horizontal)

        self.table = QTableWidget(0, len(self.columns))
        self.table.setHorizontalHeaderLabels([label for label, _ in self.columns])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        splitter.addWidget(self.table)

        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.addWidget(QLabel("Details"))

        self.details = QTextEdit()
        self.details.setReadOnly(True)
        details_layout.addWidget(self.details)

        splitter.addWidget(details_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

    def refresh(self) -> None:
        try:
            self._all_records = list(self.load_records())
        except Exception as exc:  # pragma: no cover - UI feedback only
            self._all_records = []
            self._show_error(f"Failed to load {self.title}: {exc}")

        self._apply_filter(self.filter_input.text())

    def selected_record(self) -> object | None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        if row < 0 or row >= len(self.records):
            return None
        return self.records[row]

    def selected_id(self) -> str | None:
        record = self.selected_record()
        if record is None:
            return None
        data = asdict(record)
        return str(data.get("id")) if data.get("id") else None

    def _on_selection_changed(self) -> None:
        record = self.selected_record()
        self._update_details(record)

    def _update_details(self, record: object | None) -> None:
        if record is None:
            self.details.setPlainText("Select a row to see details.")
            return
        self.details.setPlainText(self.format_details(record))

    def _apply_filter(self, text: str) -> None:
        query = text.strip().lower()
        if query == "":
            self.records = list(self._all_records)
        else:
            self.records = [record for record in self._all_records if self._matches(record, query)]
        self._render_records()

    def _matches(self, record: object, query: str) -> bool:
        for _, getter in self.columns:
            value = _fmt(getter(record)).lower()
            if query in value:
                return True
        return False

    def _render_records(self) -> None:
        self.table.setRowCount(len(self.records))
        for row_index, record in enumerate(self.records):
            for col_index, (_, getter) in enumerate(self.columns):
                value = _truncate(getter(record))
                item = QTableWidgetItem(value)
                item.setToolTip(_fmt(getter(record)))
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.table.setItem(row_index, col_index, item)

        total = len(self._all_records)
        shown = len(self.records)
        if self.filter_input.text().strip():
            self.count_label.setText(f"Count: {shown} (filtered from {total})")
        else:
            self.count_label.setText(f"Count: {shown}")

        self.table.clearSelection()
        self._update_details(None)

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Specs Updates UI")
        self.resize(1200, 800)

        central = QWidget()
        layout = QVBoxLayout(central)

        actions_layout = QHBoxLayout()

        self.ingest_button = QPushButton("Ingest")
        self.ingest_button.clicked.connect(self.handle_ingest)
        actions_layout.addWidget(self.ingest_button)

        self.transform_artifacts_button = QPushButton("Transform Artifacts")
        self.transform_artifacts_button.clicked.connect(self.handle_transform_artifacts)
        actions_layout.addWidget(self.transform_artifacts_button)

        self.transform_oq_button = QPushButton("Transform OQs")
        self.transform_oq_button.clicked.connect(self.handle_transform_oq)
        actions_layout.addWidget(self.transform_oq_button)

        self.decide_oq_button = QPushButton("Decide OQ")
        self.decide_oq_button.clicked.connect(self.handle_decide_oq)
        actions_layout.addWidget(self.decide_oq_button)

        self.approve_pu_button = QPushButton("Approve PU")
        self.approve_pu_button.clicked.connect(self.handle_approve_pu)
        actions_layout.addWidget(self.approve_pu_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_all)
        actions_layout.addWidget(self.refresh_button)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.setCentralWidget(central)

        self._build_tabs()
        self.refresh_all()

    def _build_tabs(self) -> None:
        self.artifacts_tab = RecordsTab(
            title="Artifacts",
            columns=[
                ("ID", lambda a: a.id),
                ("Type", lambda a: a.type.value if hasattr(a.type, "value") else a.type),
                ("Status", lambda a: a.status),
                ("Rephrasing", lambda a: a.rephrasing),
            ],
            load_records=self._load_artifacts,
            format_details=_format_artifact_details,
        )
        self.tabs.addTab(self.artifacts_tab, "Artifacts")

        self.oq_tab = RecordsTab(
            title="Open Questions",
            columns=[
                ("ID", lambda o: o.id),
                ("Status", lambda o: o.status),
                ("Question", lambda o: o.question),
                ("Decision", lambda o: o.decision),
            ],
            load_records=self._load_open_questions,
            format_details=_format_open_question_details,
        )
        self.tabs.addTab(self.oq_tab, "Open Questions")

        self.pu_tab = RecordsTab(
            title="Proposed Updates",
            columns=[
                ("ID", lambda p: p.id),
                ("Status", lambda p: p.status),
                ("Rephrasing", lambda p: p.rephrasing),
                ("Decision", lambda p: p.decision),
            ],
            load_records=self._load_proposed_updates,
            format_details=_format_proposed_update_details,
        )
        self.tabs.addTab(self.pu_tab, "Proposed Updates")

    def refresh_all(self) -> None:
        self.artifacts_tab.refresh()
        self.oq_tab.refresh()
        self.pu_tab.refresh()
        self.statusBar().showMessage("Data refreshed", 3000)

    def handle_ingest(self) -> None:
        default_channel = os.getenv("SLACK_CHANNEL_ID", "general")
        channel, ok = QInputDialog.getText(
            self,
            "Ingest",
            "Slack channel ID",
            text=default_channel,
        )
        if not ok or channel.strip() == "":
            return

        try:
            ingest_use_case = build_ingest_use_case()
            result = ingest_use_case.execute(channel.strip())
        except Exception as exc:  # pragma: no cover - UI feedback only
            QMessageBox.critical(self, "Ingest failed", str(exc))
            return

        if result.threads_fetched == 0:
            QMessageBox.information(self, "Ingest", "No new threads found.")
        else:
            message = (
                f"Created {result.artifacts_created} artifacts. "
                f"OQ: {result.oq_count}, PU: {result.pu_count}, "
                f"IRRELEVANT: {result.irrelevant_count}."
            )
            QMessageBox.information(self, "Ingest", message)

        self.refresh_all()

    def handle_transform_artifacts(self) -> None:
        try:
            use_case = build_transform_artifacts_use_case()
            oq_count, pu_count = use_case.execute()
        except Exception as exc:  # pragma: no cover - UI feedback only
            QMessageBox.critical(self, "Transform failed", str(exc))
            return

        QMessageBox.information(
            self,
            "Transform Artifacts",
            f"Created {oq_count} OQ and {pu_count} PU.",
        )
        self.refresh_all()

    def handle_transform_oq(self) -> None:
        try:
            use_case = build_transform_oq_use_case()
            result = use_case.execute()
        except Exception as exc:  # pragma: no cover - UI feedback only
            QMessageBox.critical(self, "Transform failed", str(exc))
            return

        QMessageBox.information(
            self,
            "Transform OQs",
            f"Created {result.transformed_count} proposed updates.",
        )
        self.refresh_all()

    def handle_decide_oq(self) -> None:
        oq_id = self.oq_tab.selected_id()
        if not oq_id:
            QMessageBox.information(self, "Decide OQ", "Select an OQ first.")
            return

        dialog = DecisionDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        decision, rationale = dialog.values()
        if decision == "" or rationale == "":
            QMessageBox.warning(self, "Decide OQ", "Decision and rationale are required.")
            return

        try:
            use_case = build_add_decision_use_case()
            result = use_case.execute(oq_id, decision, rationale)
        except Exception as exc:  # pragma: no cover - UI feedback only
            QMessageBox.critical(self, "Decide OQ", str(exc))
            return

        if not result.updated:
            QMessageBox.warning(self, "Decide OQ", f"OQ {oq_id} not found.")
        else:
            QMessageBox.information(self, "Decide OQ", f"Decision saved for {oq_id}.")
            self.refresh_all()

    def handle_approve_pu(self) -> None:
        pu_id = self.pu_tab.selected_id()
        if not pu_id:
            QMessageBox.information(self, "Approve PU", "Select a proposed update first.")
            return

        try:
            use_case = build_approve_pu_use_case()
            result = use_case.execute(pu_id)
        except Exception as exc:  # pragma: no cover - UI feedback only
            QMessageBox.critical(self, "Approve PU", str(exc))
            return

        if result.spec_update is None:
            QMessageBox.warning(self, "Approve PU", f"PU {pu_id} not found.")
            return

        remaining = result.remaining_drafts
        message = f"Approved {pu_id}. Remaining drafts: {remaining}."
        QMessageBox.information(self, "Approve PU", message)
        self.refresh_all()

    @staticmethod
    def _load_artifacts() -> Iterable[object]:
        use_case = build_list_artifacts_use_case()
        return use_case.execute()

    @staticmethod
    def _load_open_questions() -> Iterable[object]:
        use_case = build_list_open_questions_use_case()
        return use_case.execute()

    @staticmethod
    def _load_proposed_updates() -> Iterable[object]:
        use_case = build_list_proposed_updates_use_case()
        return use_case.execute()


def _format_artifact_details(artifact: object) -> str:
    data = asdict(artifact)
    artifact_type = data.get("type")
    if hasattr(artifact_type, "value"):
        artifact_type = artifact_type.value
    lines = [
        f"ID: {_fmt(data.get('id'))}",
        f"Conversation ID: {_fmt(data.get('conversation_id'))}",
        f"Type: {_fmt(artifact_type)}",
        f"Status: {_fmt(data.get('status'))}",
        "",
        "Rephrasing:",
        _fmt(data.get("rephrasing")),
        "",
        "Rationale:",
        _fmt(data.get("rationale")),
        "",
        "Summary of context:",
        _fmt(data.get("summary_of_context")),
    ]
    return "\n".join(lines)


def _format_open_question_details(oq: object) -> str:
    data = asdict(oq)
    lines = [
        f"ID: {_fmt(data.get('id'))}",
        f"Artifact ID: {_fmt(data.get('artifact_id'))}",
        f"Status: {_fmt(data.get('status'))}",
        f"Slack TS: {_fmt(data.get('slack_ts'))}",
        "",
        "Question:",
        _fmt(data.get("question")),
        "",
        "Context:",
        _fmt(data.get("context")),
        "",
        "Decision:",
        _fmt(data.get("decision")),
        "",
        "Decision rationale:",
        _fmt(data.get("decision_rationale")),
    ]
    return "\n".join(lines)


def _format_proposed_update_details(pu: object) -> str:
    data = asdict(pu)
    lines = [
        f"ID: {_fmt(data.get('id'))}",
        f"Artifact ID: {_fmt(data.get('artifact_id'))}",
        f"Source OQ ID: {_fmt(data.get('source_oq_id'))}",
        f"Status: {_fmt(data.get('status'))}",
        "",
        "Rephrasing:",
        _fmt(data.get("rephrasing")),
        "",
        "Context:",
        _fmt(data.get("context")),
        "",
        "Decision:",
        _fmt(data.get("decision")),
        "",
        "Rationale:",
        _fmt(data.get("rationale")),
    ]
    return "\n".join(lines)


def main() -> None:
    load_dotenv(override=True)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
