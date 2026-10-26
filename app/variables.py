"""
Dynamic Variables Resolver
Parses and replaces dynamic placeholders in snippet replacement strings.
Supported placeholders:
- {{date}} -> 2026-08-27
- {{date:FORMAT}} -> custom format, e.g. {{date:%Y/%m/%d}} or {{date:%Y年%m月%d日}}
- {{time}} -> 14:30:15
- {{time:FORMAT}} -> custom format, e.g. {{time:%H:%M}}
- {{datetime}} -> 2026-08-27 14:30:15
- {{year}}, {{month}}, {{day}}, {{weekday}}
- {{clipboard}} -> text currently in clipboard
- {{uuid}} -> 36-char UUID4
- {{timestamp}} -> Unix timestamp
- {{cursor}} -> marks cursor position (will calculate cursor offset)
"""

import datetime
import re
import uuid
import pyperclip


def get_weekday_cn(dt: datetime.datetime) -> str:
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return weekdays[dt.weekday()]


def resolve_variables(text: str) -> tuple[str, int]:
    """
    Resolves all dynamic placeholders in the text.
    Returns:
        (resolved_text, cursor_offset_from_end)
        cursor_offset_from_end: number of left arrow presses needed if {{cursor}} was used, else 0.
    """
    if not text:
        return "", 0

    now = datetime.datetime.now()

    # 1. Custom date: {{date:FORMAT}}
    def replace_custom_date(match):
        fmt = match.group(1)
        try:
            return now.strftime(fmt)
        except Exception:
            return match.group(0)

    text = re.sub(r"\{\{date:([^\}]+)\}\}", replace_custom_date, text)

    # 2. Custom time: {{time:FORMAT}}
    def replace_custom_time(match):
        fmt = match.group(1)
        try:
            return now.strftime(fmt)
        except Exception:
            return match.group(0)

    text = re.sub(r"\{\{time:([^\}]+)\}\}", replace_custom_time, text)

    # 3. Standard date / time placeholders
    text = text.replace("{{date}}", now.strftime("%Y-%m-%d"))
    text = text.replace("{{time}}", now.strftime("%H:%M:%S"))
    text = text.replace("{{datetime}}", now.strftime("%Y-%m-%d %H:%M:%S"))
    text = text.replace("{{year}}", now.strftime("%Y"))
    text = text.replace("{{month}}", now.strftime("%m"))
    text = text.replace("{{day}}", now.strftime("%d"))
    text = text.replace("{{weekday}}", get_weekday_cn(now))
    text = text.replace("{{timestamp}}", str(int(now.timestamp())))

    # 4. UUID / GUID
    if "{{uuid}}" in text:
        text = text.replace("{{uuid}}", str(uuid.uuid4()))
    if "{{guid}}" in text:
        text = text.replace("{{guid}}", str(uuid.uuid4()).upper())

    # 5. Clipboard
    if "{{clipboard}}" in text:
        try:
            cb_text = pyperclip.paste() or ""
        except Exception:
            cb_text = ""
        text = text.replace("{{clipboard}}", cb_text)

    # 6. Cursor position placeholder {{cursor}}
    cursor_offset = 0
    if "{{cursor}}" in text:
        idx = text.find("{{cursor}}")
        text = text.replace("{{cursor}}", "")
        # Number of chars from cursor position to end of string
        cursor_offset = len(text) - idx

    return text, cursor_offset
