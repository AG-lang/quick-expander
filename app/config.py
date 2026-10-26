"""
Configuration & Snippet Storage Manager
Handles loading, saving, importing, exporting snippet rules, categories, and user preferences.
"""

import json
import os
import csv
import uuid
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SNIPPETS_FILE = DATA_DIR / "snippets.json"
CONFIG_FILE = DATA_DIR / "config.json"

DEFAULT_CATEGORIES = ["快捷编码", "个人信息", "工作模版", "动态宏"]

DEFAULT_CONFIG = {
    "enabled": True,
    "hotkey_toggle": "<ctrl>+<alt>+s",
    "autostart": False,
    "start_minimized": False,
    "play_sound": False,
    "show_notification": True,
    "theme": "dark",
    "default_method": "auto",
    "backspace_delay_ms": 5,
    "custom_categories": DEFAULT_CATEGORIES.copy(),
}

DEFAULT_SNIPPETS = [
    {
        "id": "rule_411",
        "trigger": "411",
        "replacement": "4113293000",
        "description": "快捷编号补全 (示例)",
        "category": "快捷编码",
        "enabled": True,
        "match_case": True,
        "mode": "instant",
        "method": "auto",
        "use_count": 0,
        "created_at": "2026-08-27 00:00:00",
    },
    {
        "id": "rule_email",
        "trigger": "@@em",
        "replacement": "myemail@company.com",
        "description": "常用工作邮箱",
        "category": "个人信息",
        "enabled": True,
        "match_case": True,
        "mode": "instant",
        "method": "auto",
        "use_count": 0,
        "created_at": "2026-08-27 00:00:00",
    },
    {
        "id": "rule_phone",
        "trigger": "@@phone",
        "replacement": "13800138000",
        "description": "常用手机号码",
        "category": "个人信息",
        "enabled": True,
        "match_case": True,
        "mode": "instant",
        "method": "auto",
        "use_count": 0,
        "created_at": "2026-08-27 00:00:00",
    },
    {
        "id": "rule_addr",
        "trigger": "@@addr",
        "replacement": "北京市海淀区中关村南大街1号",
        "description": "常用收货地址",
        "category": "个人信息",
        "enabled": True,
        "match_case": True,
        "mode": "instant",
        "method": "auto",
        "use_count": 0,
        "created_at": "2026-08-27 00:00:00",
    },
    {
        "id": "rule_date",
        "trigger": "//date",
        "replacement": "{{date}}",
        "description": "快速插入当前日期 (年-月-日)",
        "category": "动态宏",
        "enabled": True,
        "match_case": True,
        "mode": "instant",
        "method": "auto",
        "use_count": 0,
        "created_at": "2026-08-27 00:00:00",
    },
    {
        "id": "rule_time",
        "trigger": "//time",
        "replacement": "{{time}}",
        "description": "快速插入当前时间 (时:分:秒)",
        "category": "动态宏",
        "enabled": True,
        "match_case": True,
        "mode": "instant",
        "method": "auto",
        "use_count": 0,
        "created_at": "2026-08-27 00:00:00",
    },
    {
        "id": "rule_now",
        "trigger": "//now",
        "replacement": "{{datetime}} {{weekday}}",
        "description": "快速插入完整日期时间与星期",
        "category": "动态宏",
        "enabled": True,
        "match_case": True,
        "mode": "instant",
        "method": "auto",
        "use_count": 0,
        "created_at": "2026-08-27 00:00:00",
    },
    {
        "id": "rule_uuid",
        "trigger": "//uuid",
        "replacement": "{{uuid}}",
        "description": "快速生成随机 UUID4",
        "category": "动态宏",
        "enabled": True,
        "match_case": True,
        "mode": "instant",
        "method": "auto",
        "use_count": 0,
        "created_at": "2026-08-27 00:00:00",
    },
]


class ConfigManager:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
        self.snippets = self._load_snippets()
        self._ensure_category_migration()

    def _load_config(self) -> dict:
        if not CONFIG_FILE.exists():
            self._save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                cfg = DEFAULT_CONFIG.copy()
                cfg.update(data)
                return cfg
        except Exception:
            return DEFAULT_CONFIG.copy()

    def _save_config(self, cfg: dict):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)

    def save_config(self):
        self._save_config(self.config)

    def _load_snippets(self) -> list[dict]:
        if not SNIPPETS_FILE.exists():
            self._save_snippets(DEFAULT_SNIPPETS)
            return [s.copy() for s in DEFAULT_SNIPPETS]
        try:
            with open(SNIPPETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return [s.copy() for s in DEFAULT_SNIPPETS]

    def _save_snippets(self, snippets: list[dict]):
        with open(SNIPPETS_FILE, "w", encoding="utf-8") as f:
            json.dump(snippets, f, ensure_ascii=False, indent=2)

    def save_snippets(self):
        self._save_snippets(self.snippets)

    def _ensure_category_migration(self):
        """Ensures all snippets have a valid category attribute."""
        updated = False
        for s in self.snippets:
            if "category" not in s or not s["category"]:
                # Infer default category
                trig = s.get("trigger", "")
                if trig.isdigit():
                    s["category"] = "快捷编码"
                elif trig.startswith("//"):
                    s["category"] = "动态宏"
                elif trig.startswith("@@"):
                    s["category"] = "个人信息"
                else:
                    s["category"] = "快捷编码"
                updated = True
        if updated:
            self.save_snippets()

    # --- Categories CRUD ---
    def get_categories(self) -> list[str]:
        """Returns the list of distinct categories in display order."""
        cats_set = set(self.config.get("custom_categories", DEFAULT_CATEGORIES))
        for s in self.snippets:
            c = s.get("category")
            if c:
                cats_set.add(c)
        
        # Keep consistent order
        ordered = []
        for default_cat in DEFAULT_CATEGORIES:
            if default_cat in cats_set:
                ordered.append(default_cat)
                cats_set.remove(default_cat)
        ordered.extend(sorted(cats_set))
        return ordered

    def add_category(self, name: str) -> bool:
        name = name.strip()
        if not name:
            return False
        cats = self.get_categories()
        if name in cats:
            return False
        custom_cats = self.config.get("custom_categories", DEFAULT_CATEGORIES.copy())
        if name not in custom_cats:
            custom_cats.append(name)
            self.config["custom_categories"] = custom_cats
            self.save_config()
        return True

    def rename_category(self, old_name: str, new_name: str) -> bool:
        old_name = old_name.strip()
        new_name = new_name.strip()
        if not old_name or not new_name or old_name == new_name:
            return False
        
        # Update snippets
        for s in self.snippets:
            if s.get("category") == old_name:
                s["category"] = new_name
        self.save_snippets()

        # Update config custom_categories
        custom_cats = self.config.get("custom_categories", DEFAULT_CATEGORIES.copy())
        if old_name in custom_cats:
            idx = custom_cats.index(old_name)
            custom_cats[idx] = new_name
            self.config["custom_categories"] = custom_cats
            self.save_config()
        return True

    def delete_category(self, name: str) -> bool:
        name = name.strip()
        if not name:
            return False
        # Move all snippets in this category to first remaining category or '快捷编码'
        remaining_cats = [c for c in self.get_categories() if c != name]
        fallback_cat = remaining_cats[0] if remaining_cats else "快捷编码"

        for s in self.snippets:
            if s.get("category") == name:
                s["category"] = fallback_cat
        self.save_snippets()

        custom_cats = self.config.get("custom_categories", DEFAULT_CATEGORIES.copy())
        if name in custom_cats:
            custom_cats.remove(name)
            self.config["custom_categories"] = custom_cats
            self.save_config()
        return True

    # --- Snippets CRUD ---
    def get_enabled_snippets(self) -> list[dict]:
        return [s for s in self.snippets if s.get("enabled", True)]

    def add_snippet(
        self,
        trigger: str,
        replacement: str,
        description: str = "",
        category: str = "快捷编码",
        match_case: bool = True,
        mode: str = "instant",
        method: str = "auto",
    ) -> dict:
        rule = {
            "id": uuid.uuid4().hex[:8],
            "trigger": trigger,
            "replacement": replacement,
            "description": description,
            "category": category.strip() or "快捷编码",
            "enabled": True,
            "match_case": match_case,
            "mode": mode,
            "method": method,
            "use_count": 0,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.snippets.append(rule)
        self.save_snippets()
        return rule

    def update_snippet(self, rule_id: str, **kwargs) -> bool:
        for s in self.snippets:
            if s["id"] == rule_id:
                s.update(kwargs)
                self.save_snippets()
                return True
        return False

    def delete_snippet(self, rule_id: str) -> bool:
        initial_len = len(self.snippets)
        self.snippets = [s for s in self.snippets if s["id"] != rule_id]
        if len(self.snippets) != initial_len:
            self.save_snippets()
            return True
        return False

    def toggle_snippet(self, rule_id: str) -> bool:
        for s in self.snippets:
            if s["id"] == rule_id:
                s["enabled"] = not s.get("enabled", True)
                self.save_snippets()
                return s["enabled"]
        return False

    def increment_use_count(self, rule_id: str):
        for s in self.snippets:
            if s["id"] == rule_id:
                s["use_count"] = s.get("use_count", 0) + 1
                self.save_snippets()
                break

    # --- Import / Export ---
    def export_json(self, target_path: str):
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.snippets, f, ensure_ascii=False, indent=2)

    def import_json(self, source_path: str, overwrite: bool = False) -> int:
        with open(source_path, "r", encoding="utf-8") as f:
            imported = json.load(f)
        if not isinstance(imported, list):
            raise ValueError("导入的 JSON 必须是规则列表")

        if overwrite:
            self.snippets = imported
            count = len(imported)
        else:
            existing_ids = {s.get("id") for s in self.snippets}
            count = 0
            for item in imported:
                if "trigger" in item and "replacement" in item:
                    if item.get("id") not in existing_ids:
                        if "id" not in item:
                            item["id"] = uuid.uuid4().hex[:8]
                        if "category" not in item:
                            item["category"] = "快捷编码"
                        self.snippets.append(item)
                        existing_ids.add(item["id"])
                        count += 1
        self._ensure_category_migration()
        self.save_snippets()
        return count

    def export_csv(self, target_path: str):
        with open(target_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["触发词", "替换内容", "说明", "分类", "是否启用", "区分大小写", "触发模式", "注入方式"])
            for s in self.snippets:
                writer.writerow([
                    s.get("trigger", ""),
                    s.get("replacement", ""),
                    s.get("description", ""),
                    s.get("category", "快捷编码"),
                    "是" if s.get("enabled", True) else "否",
                    "是" if s.get("match_case", False) else "否",
                    s.get("mode", "instant"),
                    s.get("method", "auto"),
                ])

    def import_csv(self, source_path: str, overwrite: bool = False) -> int:
        with open(source_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            return 0

        # Skip header if present
        if "触发词" in rows[0][0] or "trigger" in rows[0][0].lower():
            rows = rows[1:]

        if overwrite:
            self.snippets = []

        count = 0
        for row in rows:
            if len(row) >= 2 and row[0].strip():
                trigger = row[0].strip()
                replacement = row[1]
                desc = row[2] if len(row) > 2 else ""
                category = row[3].strip() if len(row) > 3 and row[3].strip() else "快捷编码"
                enabled = (row[4].strip() != "否") if len(row) > 4 else True
                match_case = (row[5].strip() != "否") if len(row) > 5 and row[5].strip() else True
                mode = row[6].strip() if len(row) > 6 and row[6].strip() else "instant"
                method = row[7].strip() if len(row) > 7 and row[7].strip() else "auto"

                self.snippets.append({
                    "id": uuid.uuid4().hex[:8],
                    "trigger": trigger,
                    "replacement": replacement,
                    "description": desc,
                    "category": category,
                    "enabled": enabled,
                    "match_case": match_case,
                    "mode": mode,
                    "method": method,
                    "use_count": 0,
                    "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                count += 1

        self._ensure_category_migration()
        self.save_snippets()
        return count
