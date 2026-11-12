#!/usr/bin/env python3
"""pdf-tools — everyday PDF operations without a GUI: info, merge, split, text, fields, fill, tables.

Requires: pypdf  ->  pip install pypdf          (all commands except `tables`)
          pdfplumber -> pip install pdfplumber   (`tables` only)
Usage:
  python pdf-tools.py info   <in.pdf>                              JSON: pages, page size, encrypted, form fields, metadata
  python pdf-tools.py merge  <out.pdf> <a.pdf> <b.pdf> [...]       concatenate in the given order
  python pdf-tools.py split  <in.pdf> <out_dir> [--ranges 1-3,4,5-]  one file per range (default: one per page)
  python pdf-tools.py text   <in.pdf> [--pages 1-3]                 extracted text to stdout (pages separated by form feed)
  python pdf-tools.py fields <in.pdf>                              JSON: AcroForm field names, types, current values
  python pdf-tools.py fill   <in.pdf> <values.json> <out.pdf>      fill AcroForm fields by name; unknown names are an error
  python pdf-tools.py tables <in.pdf> <out_dir> [--pages 1-3]      every detected table as CSV (UTF-8 with BOM, opens in Excel)
Exit: 0 ok · 1 bad input · 2 usage · 3 missing dependency.
Scanned PDFs have no text layer: `text` returns nothing — OCR is a separate step (see skills/docs-pdf/SKILL.md).
"""
import csv
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def need(module, package):
    try:
        return __import__(module)
    except ImportError:
        sys.stderr.write(f"pdf-tools: missing Python library {package}.\nInstall it with:  pip install {package}\n")
        sys.exit(3)


class InputError(Exception):
    pass


def parse_ranges(spec, total):
    """'1-3,5,7-' -> [(0,3),(4,5),(6,total)] (0-based, end exclusive)."""
    out = []
    for part in (spec or "").split(","):
        part = part.strip()
        m = re.fullmatch(r"(\d+)?(-)?(\d+)?", part)
        if not part or not m or (not m[1] and not m[3]):
            raise InputError(f"bad page range {part!r} (use 1-3,5,7-)")
        start = int(m[1]) if m[1] else 1
        end = int(m[3]) if m[3] else (total if m[2] else start)
        if not 1 <= start <= end <= total:
            raise InputError(f"page range {part!r} is outside 1-{total}")
        out.append((start - 1, end))
    return out


def opt(args, name, default=None):
    if name in args:
        i = args.index(name)
        if i + 1 >= len(args):
            raise InputError(f"{name} needs a value")
        value = args[i + 1]
        del args[i:i + 2]
        return value
    return default


def reader(path):
    pypdf = need("pypdf", "pypdf")
    r = pypdf.PdfReader(str(path))
    if r.is_encrypted:
        try:
            r.decrypt("")
        except Exception:
            raise InputError(f"{path} is encrypted — ask the owner for the password")
    return r


def field_type(f):
    return {"/Tx": "text", "/Btn": "button", "/Ch": "choice", "/Sig": "signature"}.get(f.get("/FT"), str(f.get("/FT")))


def cmd_info(args):
    r = reader(args[0])
    box = r.pages[0].mediabox if r.pages else None
    meta = {k.lstrip("/"): str(v) for k, v in (r.metadata or {}).items()}
    print(json.dumps({"pages": len(r.pages), "encrypted": r.is_encrypted,
                      "first_page_pt": [round(float(box.width), 1), round(float(box.height), 1)] if box else None,
                      "form_fields": len(r.get_fields() or {}), "metadata": meta}, ensure_ascii=False))


def cmd_merge(args):
    pypdf = need("pypdf", "pypdf")
    out, inputs = args[0], args[1:]
    if len(inputs) < 2:
        raise InputError("merge needs at least two input files")
    w = pypdf.PdfWriter()
    for path in inputs:
        w.append(reader(path))
    with open(out, "wb") as fh:
        w.write(fh)
    print(json.dumps({"output": out, "pages": len(w.pages)}, ensure_ascii=False))


def cmd_split(args):
    pypdf = need("pypdf", "pypdf")
    ranges = opt(args, "--ranges")
    src, out_dir = Path(args[0]), Path(args[1])
    r = reader(src)
    total = len(r.pages)
    spans = parse_ranges(ranges, total) if ranges else [(i, i + 1) for i in range(total)]
    out_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for a, b in spans:
        w = pypdf.PdfWriter()
        for i in range(a, b):
            w.add_page(r.pages[i])
        name = out_dir / (f"{src.stem}_p{a + 1}.pdf" if b - a == 1 else f"{src.stem}_p{a + 1}-{b}.pdf")
        with open(name, "wb") as fh:
            w.write(fh)
        files.append(str(name))
    print(json.dumps({"files": files}, ensure_ascii=False))


def cmd_text(args):
    pages = opt(args, "--pages")
    r = reader(args[0])
    spans = parse_ranges(pages, len(r.pages)) if pages else [(0, len(r.pages))]
    chunks = [r.pages[i].extract_text() or "" for a, b in spans for i in range(a, b)]
    sys.stdout.write("\f".join(chunks))
    if not any(c.strip() for c in chunks):
        sys.stderr.write("pdf-tools: no text layer found — the PDF is probably scanned; run OCR first\n")


def cmd_fields(args):
    r = reader(args[0])
    fields = r.get_fields() or {}
    out = []
    for name, f in fields.items():
        item = {"name": name, "type": field_type(f), "value": None if f.get("/V") is None else str(f.get("/V"))}
        if f.get("/_States_"):
            item["states"] = [str(s) for s in f["/_States_"]]
        if f.get("/Opt"):
            item["options"] = [str(o) for o in f["/Opt"]]
        out.append(item)
    print(json.dumps(out, ensure_ascii=False, indent=1))


def cmd_fill(args):
    pypdf = need("pypdf", "pypdf")
    src, values_path, out = args[0], Path(args[1]), args[2]
    values = json.loads(values_path.read_text(encoding="utf-8"))
    r = reader(src)
    known = r.get_fields() or {}
    if not known:
        raise InputError(f"{src} has no AcroForm fields — it is a flat PDF; overlay text instead (see skills/docs-pdf/SKILL.md)")
    unknown = [k for k in values if k not in known]
    if unknown:
        raise InputError(f"unknown field names: {', '.join(unknown)} (run `fields` to list them)")
    w = pypdf.PdfWriter(clone_from=r)
    for page in w.pages:
        w.update_page_form_field_values(page, {k: str(v) for k, v in values.items()}, auto_regenerate=False)
    w.set_need_appearances_writer(True)  # viewers rebuild appearances — needed for Cyrillic values
    with open(out, "wb") as fh:
        w.write(fh)
    print(json.dumps({"output": out, "filled": len(values)}, ensure_ascii=False))


def cmd_tables(args):
    pdfplumber = need("pdfplumber", "pdfplumber")
    pages = opt(args, "--pages")
    src, out_dir = Path(args[0]), Path(args[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    files = []
    with pdfplumber.open(str(src)) as pdf:
        spans = parse_ranges(pages, len(pdf.pages)) if pages else [(0, len(pdf.pages))]
        for a, b in spans:
            for i in range(a, b):
                for t, table in enumerate(pdf.pages[i].extract_tables(), 1):
                    name = out_dir / f"{src.stem}_p{i + 1}_t{t}.csv"
                    with open(name, "w", newline="", encoding="utf-8-sig") as fh:
                        csv.writer(fh).writerows(table)
                    files.append(str(name))
    print(json.dumps({"tables": files}, ensure_ascii=False))


# name: (handler, minimum positional args, which positional args are input files)
COMMANDS = {"info": (cmd_info, 1, slice(0, 1)), "merge": (cmd_merge, 3, slice(1, None)), "split": (cmd_split, 2, slice(0, 1)),
            "text": (cmd_text, 1, slice(0, 1)), "fields": (cmd_fields, 1, slice(0, 1)), "fill": (cmd_fill, 3, slice(0, 2)),
            "tables": (cmd_tables, 2, slice(0, 1))}


def main(argv):
    if not argv or argv[0] in ("-h", "--help") or argv[0] not in COMMANDS:
        print(__doc__.strip())
        return 0 if argv[:1] in (["-h"], ["--help"]) else 2
    fn, min_args, inputs = COMMANDS[argv[0]]
    args = argv[1:]
    try:
        positional = [a for i, a in enumerate(args) if not a.startswith("--") and not (i and args[i - 1].startswith("--"))]
        if len(positional) < min_args:
            raise InputError(f"{argv[0]} needs {min_args} argument(s); see --help")
        for path in positional[inputs]:
            if not Path(path).is_file():
                raise InputError(f"file not found: {path}")
        fn(args)
    except InputError as e:
        print(f"pdf-tools: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # pypdf raises its own error types for damaged files
        print(f"pdf-tools: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
