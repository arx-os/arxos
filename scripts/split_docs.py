#!/usr/bin/env python3
"""Utility to split large Rust documentation markdown files into chapter modules."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

TOC_PATTERN = re.compile(r"^(\d+(?:\.\d+)*)\.\s+(.*)$")


@dataclass
class TocEntry:
    number: str
    title: str


def parse_toc(lines: List[str]) -> Tuple[List[TocEntry], List[str], int]:
    entries: List[TocEntry] = []
    preface_before: List[str] = []
    toc_started = False
    toc_end_idx = len(lines)

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            if toc_started:
                continue
            preface_before.append(line)
            continue
        match = TOC_PATTERN.match(stripped)
        if match:
            entries.append(TocEntry(match.group(1), match.group(2)))
            toc_started = True
            continue
        if toc_started:
            toc_end_idx = idx
            break
        preface_before.append(line)
    else:
        toc_end_idx = len(lines)

    return entries, preface_before, toc_end_idx


def find_position(
    title: str,
    lines: List[str],
    start_idx: int,
    end_idx: int,
    aliases: Dict[str, List[str]],
) -> int | None:
    candidates = [title]
    candidates.extend(aliases.get(title, []))

    for cand in candidates:
        cand_norm = cand.strip()
        for idx in range(start_idx, end_idx):
            if lines[idx].strip() == cand_norm:
                return idx

    for cand in candidates:
        cand_lower = cand.strip().lower()
        if not cand_lower:
            continue
        for idx in range(start_idx, end_idx):
            if cand_lower in lines[idx].strip().lower():
                return idx

    words = [w.lower() for w in re.findall(r"\w+", title) if len(w) > 2]
    if words:
        for idx in range(start_idx, end_idx):
            text = lines[idx].strip().lower()
            if text and all(word in text for word in words):
                return idx
    return None


def slugify(title: str, existing: Dict[str, str]) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "section"
    base = slug
    counter = 2
    while slug in existing.values():
        slug = f"{base}-{counter}"
        counter += 1
    return slug



def _downgrade_heading(line: str) -> str:
    if not line.startswith('#'):
        return line
    hashes = len(line) - len(line.lstrip('#'))
    if hashes <= 1:
        return line
    return '#' * (hashes - 1) + line[hashes:]


def split_markdown_by_headings(path: Path) -> None:
    lines = path.read_text().splitlines()
    title = None
    title_idx = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('# '):
            title = stripped[2:].strip()
            title_idx = idx
            break
        if title is None:
            title = stripped
            title_idx = idx
            break
    if title is None:
        raise RuntimeError(f"Unable to determine title in {path}")

    sections: List[Tuple[str, int]] = []
    for idx, line in enumerate(lines):
        if line.startswith('## '):
            sections.append((line[3:].strip(), idx))
    if not sections:
        raise RuntimeError(f"No '##' sections found in {path}")

    out_dir = path.with_suffix('')
    out_dir.mkdir(parents=True, exist_ok=True)
    for existing in out_dir.glob('ch*.md'):
        existing.unlink()
    index_path = out_dir / 'index.md'
    if index_path.exists():
        index_path.unlink()

    preface_lines = []
    first_section_idx = sections[0][1]
    for line in lines[title_idx + 1:first_section_idx]:
        preface_lines.append(line)
    preface = '\n'.join(preface_lines).strip('\n')

    slug_map: Dict[str, str] = {}
    index_lines: List[str] = [f"# {title}", ""]
    if preface:
        index_lines.extend([preface, ""])
    index_lines.append('## Chapters')

    for i, (section_title, start_idx) in enumerate(sections):
        slug = slugify(section_title, slug_map)
        slug_map[section_title] = slug
        index_lines.append(f"- [{section_title}](ch{(i+1):02d}-{slug}.md)")
        end_idx = sections[i + 1][1] if i + 1 < len(sections) else len(lines)
        body_lines = []
        for line in lines[start_idx + 1:end_idx]:
            body_lines.append(_downgrade_heading(line))
        while body_lines and not body_lines[0].strip():
            body_lines.pop(0)
        while body_lines and not body_lines[-1].strip():
            body_lines.pop()
        content = '\n'.join([f"# {section_title}"] + body_lines) + '\n'
        (out_dir / f"ch{(i+1):02d}-{slug}.md").write_text(content)

    index_path.write_text('\n'.join(index_lines) + '\n')
    print(f"Split {path} into {len(sections)} chapters -> {out_dir}")

def split_markdown(path: Path, aliases: Dict[str, List[str]]) -> None:
    lines = path.read_text().splitlines()
    entries, preface_before, toc_end_idx = parse_toc(lines)
    if not entries:
        split_markdown_by_headings(path)
        return

    top_entries = [entry for entry in entries if entry.number.count(".") == 0]
    search_start = toc_end_idx
    top_positions: List[Tuple[str, str, int]] = []
    for entry in top_entries:
        idx = find_position(entry.title, lines, search_start, len(lines), aliases)
        if idx is None:
            raise RuntimeError(
                f"Missing heading for top-level section {entry.number} {entry.title}"
            )
        top_positions.append((entry.number, entry.title, idx))
        search_start = idx + 1

    boundaries: Dict[str, Tuple[int, int]] = {}
    for i, (number, _title, idx) in enumerate(top_positions):
        end = top_positions[i + 1][2] if i + 1 < len(top_positions) else len(lines)
        boundaries[number] = (idx, end)

    top_index_map = {num: idx for num, _title, idx in top_positions}

    positions: List[Tuple[str, str, int | None]] = []
    for entry in entries:
        if entry.number.count(".") == 0:
            idx = top_index_map[entry.number]
        else:
            parent = entry.number.split(".")[0]
            start, end = boundaries[parent]
            idx = find_position(entry.title, lines, start, end, aliases)
        positions.append((entry.number, entry.title, idx))

    book_title = None
    first_heading_idx = top_positions[0][2]
    preface_lines = list(preface_before)
    for idx in range(toc_end_idx, first_heading_idx):
        line = lines[idx]
        if book_title is None and line.strip():
            book_title = line.strip()
        else:
            preface_lines.append(line)
    if book_title is None:
        book_title = path.stem.replace("_", " ").title()
    preface_body = "\n".join(preface_lines).strip("\n")

    out_dir = path.with_suffix("")
    out_dir.mkdir(parents=True, exist_ok=True)

    for existing in out_dir.glob("ch*.md"):
        existing.unlink()
    index_path = out_dir / "index.md"
    if index_path.exists():
        index_path.unlink()

    slug_map: Dict[str, str] = {}
    chapter_entries: List[Tuple[str, str, str, int]] = []
    for number, title, idx in top_positions:
        slug = slugify(title, slug_map)
        slug_map[number] = slug
        chapter_entries.append((number, title, slug, idx))

    index_lines: List[str] = [f"# {book_title}", ""]
    if preface_body:
        index_lines.extend([preface_body, ""])
    index_lines.append("## Chapters")
    for number, title, slug, _idx in chapter_entries:
        index_lines.append(f"- [{number}. {title}](ch{int(number):02d}-{slug}.md)")
    index_path.write_text("\n".join(index_lines) + "\n")

    heading_lookup: Dict[int, Tuple[int, str]] = {}
    for number, title, idx in positions:
        if idx is None:
            continue
        level = number.count(".") + 1
        heading_lookup[idx] = (level, title)

    for i, (number, title, slug, start_idx) in enumerate(chapter_entries):
        end_idx = chapter_entries[i + 1][3] if i + 1 < len(chapter_entries) else len(lines)
        chunk_lines: List[str] = []
        for abs_idx in range(start_idx, end_idx):
            if abs_idx == start_idx:
                continue
            line = lines[abs_idx]
            if abs_idx in heading_lookup:
                level, heading_title = heading_lookup[abs_idx]
                line = f"{'#' * level} {heading_title}"
            chunk_lines.append(line)
        while chunk_lines and not chunk_lines[0].strip():
            chunk_lines.pop(0)
        while chunk_lines and not chunk_lines[-1].strip():
            chunk_lines.pop()
        output_path = out_dir / f"ch{int(number):02d}-{slug}.md"
        output_path.write_text("\n".join([f"# {title}"] + chunk_lines) + "\n")

    print(f"Split {path} into {len(chapter_entries)} chapters -> {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "files",
        nargs="+",
        help="Markdown files (relative paths) to split",
    )
    args = parser.parse_args()

    # Known overrides for section titles that don't appear verbatim in the body.
    alias_map: Dict[str, Dict[str, List[str]]] = {
        "rustdoc_book.md": {
            "In-doc settings": ["Rustdoc in-doc settings"],
            "Search": ["Rustdoc search"],
            "Rustdoc-specific lints": ["Lints"],
        },
        "cargo_book.md": {
            "Appendix: Glossary": ["Glossary"],
            "Appendix: Git Authentication": ["Git Authentication"],
        },
        "rustonomicon.md": {
            "Data Layout": ["data layout"],
            "Ownership": ["ownership"],
            "Uninitialized Memory": ["uninitialized memory"],
            "Ownership Based Resource Management": ["ownership based resource management"],
            "Concurrency": ["concurrency"],
            "Implementing Vec": ["Implementing Vec"],
            "Implementing Arc and Mutex": ["Implementing Arc and Mutex", "Implementing Arc"],
            "FFI": ["FFI"],
            "Beneath std": ["Beneath std"],
        },
        "rust_and_wasm.md": {
            "Introduction": ["Rust and WebAssembly"],
            "Background And Concepts": ["Background and Concepts"],
            "Rules": ["Rules"],
            "Implementing Life": ["Implementing Life"],
            "Testing Life": ["Testing Life"],
            "Debugging": ["Debugging"],
            "Shrinking .wasm Size": ["Shrinking .wasm Size"],
        },
        "embedded_book.md": {
            "no_std": ["no_std"],
            "Tooling": ["Tooling"],
            "Installation": ["Installation"],
            "Linux": ["Linux"],
            "MacOS": ["MacOS"],
            "Windows": ["Windows"],
            "Verify Installation": ["Verify installation"],
            "Getting started": ["Getting Started"],
        },
    }

    for file_arg in args.files:
        path = Path(file_arg)
        if not path.exists():
            path = Path("docs/rustdoc") / file_arg
        if not path.exists():
            raise FileNotFoundError(file_arg)
        aliases = alias_map.get(path.name, {})
        split_markdown(path, aliases)


if __name__ == "__main__":
    main()
