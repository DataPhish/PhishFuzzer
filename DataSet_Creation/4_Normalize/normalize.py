#!/usr/bin/env python3

import json
import os
import re
import sys
from copy import deepcopy
from typing import Any, List, Optional, Union

# ==========================
# CONFIG
# ==========================

INPUT_FILE = "emails_populated_non_manual_gemini.json"
OUTPUT_FILE = "emails_normalized.json"

# If True, remove Motivation_Gemini / URL_gemini / File_gemini after copying into canonical fields
DROP_GEMINI_FIELDS = True

# If True, add scheme to URLs that look like domains/paths without http(s)
ADD_SCHEME_IF_MISSING = True


# ==========================
# NORMALIZATION HELPERS
# ==========================

_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+\-.]*://")  # e.g., http://, https://
_DOMAINISH_RE = re.compile(
    r"^(www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(/.*)?$"
)  # rough "domain.tld/..." detector


def clean_str(s: Any) -> Optional[str]:
    if s is None:
        return None
    if not isinstance(s, str):
        s = str(s)
    s = s.strip()
    if s == "" or s.lower() == "null":
        return None
    return s


def normalize_to_str_list(value: Any, add_scheme: bool = False) -> Optional[List[str]]:
    """
    Converts:
      - None/"null"/"" -> None
      - "one" -> ["one"]
      - ["a","b"] -> ["a","b"]
    Cleans whitespace, drops empties, optionally adds http:// to scheme-less domainish strings.
    """
    if value is None:
        return None

    # Sometimes stored as "null" string
    if isinstance(value, str):
        v = clean_str(value)
        if v is None:
            return None
        items = [v]
    elif isinstance(value, list):
        items = []
        for x in value:
            cx = clean_str(x)
            if cx is not None:
                items.append(cx)
        if not items:
            return None
    else:
        # unexpected type -> stringify
        v = clean_str(value)
        if v is None:
            return None
        items = [v]

    if add_scheme:
        fixed = []
        for u in items:
            if _SCHEME_RE.match(u):
                fixed.append(u)
            else:
                # Add scheme only if it looks like a domain/path (not "mailto:", not random text)
                if _DOMAINISH_RE.match(u):
                    fixed.append("https://" + u.lstrip("/"))
                else:
                    fixed.append(u)
        items = fixed

    return items if items else None


def pick_first_present(email: dict, keys: List[str]) -> Any:
    """
    Returns the first key that exists and is not None/"null"/"".
    """
    for k in keys:
        if k not in email:
            continue
        v = email.get(k)
        if isinstance(v, str):
            if clean_str(v) is None:
                continue
        elif v is None:
            continue
        return v
    return None


# ==========================
# MAIN
# ==========================

def main():
    if not os.path.exists(INPUT_FILE):
        sys.exit(f"Input file not found: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        sys.exit("Expected the input JSON to be a list of email objects.")

    out = []
    changed = 0

    for email in data:
        e = deepcopy(email)

        # 1) Motivation canonicalization
        motivation_val = pick_first_present(e, ["Motivation", "Motivation_Gemini"])
        motivation_val = clean_str(motivation_val) or "Unknown"
        e["Motivation"] = motivation_val

        # 2) URL canonicalization (prefer URL, else URL_gemini)
        url_val = pick_first_present(e, ["URL", "URL_gemini"])
        e["URL"] = normalize_to_str_list(url_val, add_scheme=ADD_SCHEME_IF_MISSING)

        # 3) File canonicalization (prefer File, else File_gemini)
        file_val = pick_first_present(e, ["File", "File_gemini"])
        # Files usually should NOT get scheme-fixing
        e["File"] = normalize_to_str_list(file_val, add_scheme=False)

        # 4) Optionally drop gemini fields
        if DROP_GEMINI_FIELDS:
            for k in ["Motivation_Gemini", "URL_gemini", "File_gemini"]:
                if k in e:
                    del e[k]

        out.append(e)

        if e != email:
            changed += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Loaded: {len(data)} emails")
    print(f"Modified: {changed} emails")
    print(f"Wrote: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()