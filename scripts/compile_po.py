import os
import sys
import struct
from pathlib import Path

def clean_po_str(s):
    """Clean quoted PO string by unescaping standard quotes and newlines."""
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return s.replace('\\"', '"').replace('\\n', '\n')


def parse_po_file(filepath):
    """Parse .po file cleanly into dictionary of msgid -> msgstr without encoding corruption."""
    messages = {}
    current_msgid = []
    current_msgstr = []
    state = None  # None, 'msgid', 'msgstr'

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue

            if line_str.startswith("msgid "):
                if state == "msgstr":
                    msgid_key = "".join(current_msgid)
                    msgstr_val = "".join(current_msgstr)
                    messages[msgid_key] = msgstr_val
                    current_msgid = []
                    current_msgstr = []

                state = "msgid"
                raw = line_str[6:].strip()
                current_msgid.append(clean_po_str(raw))

            elif line_str.startswith("msgstr "):
                state = "msgstr"
                raw = line_str[7:].strip()
                current_msgstr.append(clean_po_str(raw))

            elif line_str.startswith('"') and line_str.endswith('"'):
                state_val = clean_po_str(line_str)
                if state == "msgid":
                    current_msgid.append(state_val)
                elif state == "msgstr":
                    current_msgstr.append(state_val)

        if state == "msgstr":
            msgid_key = "".join(current_msgid)
            msgstr_val = "".join(current_msgstr)
            messages[msgid_key] = msgstr_val

    return messages


def generate_mo(messages):
    """Generate binary MO file bytes with UTF-8 header as string 0."""
    header_str = messages.get("", "Content-Type: text/plain; charset=UTF-8\n")
    
    other_keys = sorted([k for k in messages.keys() if k != ""])
    all_keys = [""] + other_keys

    ids = []
    strs = []

    for k in all_keys:
        v = messages[k] if k != "" else header_str
        ids.append(k.encode("utf-8") + b"\x00")
        strs.append(v.encode("utf-8") + b"\x00")

    num_strings = len(ids)
    keystart = 7 * 4 + num_strings * 8 * 2
    
    koffsets = []
    voffsets = []

    kpos = 7 * 4 + num_strings * 8 * 2
    for k in ids:
        koffsets.append((len(k) - 1, kpos))
        kpos += len(k)

    vpos = kpos
    for v in strs:
        voffsets.append((len(v) - 1, vpos))
        vpos += len(v)

    mo_header = struct.pack(
        "Iiiiiii",
        0x950412DE,  # Magic number
        0,           # Revision
        num_strings, # Number of strings
        7 * 4,       # Offset of original strings table
        7 * 4 + num_strings * 8, # Offset of translation strings table
        0,           # Size of hashing table
        0            # Offset of hashing table
    )

    tbl_original = b"".join(struct.pack("II", length, offset) for length, offset in koffsets)
    tbl_translation = b"".join(struct.pack("II", length, offset) for length, offset in voffsets)
    data_original = b"".join(ids)
    data_translation = b"".join(strs)

    return mo_header + tbl_original + tbl_translation + data_original + data_translation


def compile_po_to_mo(po_filepath, mo_filepath):
    messages = parse_po_file(po_filepath)
    mo_bytes = generate_mo(messages)
    os.makedirs(os.path.dirname(mo_filepath), exist_ok=True)
    with open(mo_filepath, "wb") as f:
        f.write(mo_bytes)
    print(f"Compiled {po_filepath} -> {mo_filepath} ({len(messages)} strings)")


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    locale_dir = base_dir / "locale"
    for lang in ["en", "te", "hi"]:
        po_path = locale_dir / lang / "LC_MESSAGES" / "django.po"
        mo_path = locale_dir / lang / "LC_MESSAGES" / "django.mo"
        if po_path.exists():
            compile_po_to_mo(po_path, mo_path)
