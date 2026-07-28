#!/usr/bin/env python3
"""Append one demo-run row to the OrthoAppeals review sheet.

This runs under the gspread virtual environment, which is separate from the
harness interpreter. It reads one JSON record on stdin and appends it to the
`demo_runs` worksheet, creating that worksheet with a header row if needed.

    ~/.venvs/gsheets/bin/python scripts/sheet_log.py < record.json
"""

from __future__ import annotations

import json
import os
import sys

SPREADSHEET_ID = os.environ.get(
    "MDPLUS_RUN_LOG_SHEET_ID", "1Im48XYqt50prRy46Rvtfl7ge96hy7dA58M5wElwTHjs"
)
WORKSHEET = os.environ.get("MDPLUS_RUN_LOG_TAB", "demo_runs")
CREDENTIALS = os.environ.get(
    "MDPLUS_SHEETS_CREDENTIALS",
    os.path.expanduser("~/.config/gog/service-account.json"),
)

COLUMNS = [
    "logged_at_utc",
    "episode_id",
    "arm",
    "revision",
    "engine",
    "model",
    "run_status",
    "result_status",
    "payer",
    "plan_name",
    "state",
    "product_type",
    "procedure",
    "cpt",
    "denial_category",
    "apparent_reason",
    "selected_source_title",
    "selected_source_url",
    "evidence_role",
    "effective_date",
    "confidence_overall",
    "primary_action",
    "candidate_count",
    "citation_count",
    "question_count",
    "blocker_codes",
    "tool_events",
    "elapsed_s",
    "cost_usd",
    "validation_valid",
    "validation_errors",
    "episode_path",
    "reviewer_verdict",
    "reviewer_notes",
]


def main() -> int:
    record = json.loads(sys.stdin.read())

    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS, scopes=scopes)
    client = gspread.authorize(creds)
    book = client.open_by_key(SPREADSHEET_ID)

    try:
        sheet = book.worksheet(WORKSHEET)
    except gspread.WorksheetNotFound:
        sheet = book.add_worksheet(title=WORKSHEET, rows=1000, cols=len(COLUMNS))
        sheet.append_row(COLUMNS, value_input_option="RAW")

    header = sheet.row_values(1)
    if not header:
        sheet.append_row(COLUMNS, value_input_option="RAW")
        header = COLUMNS

    row = []
    for column in header:
        value = record.get(column, "")
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        elif value is None:
            value = ""
        row.append(str(value)[:4000])
    sheet.append_row(row, value_input_option="RAW")
    print(json.dumps({"ok": True, "worksheet": WORKSHEET, "columns": len(row)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
