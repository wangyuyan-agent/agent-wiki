#!/usr/bin/env python3
"""Build and mechanically verify the agent-wiki GitHub Pages surface.

The repository Markdown and ``protocols.yaml`` remain the source of truth.  The
builder copies those files byte-for-byte, renders a discoverable HTML view for
every Markdown document, and derives the landing page and machine entry points
from the manifest and Agent Adoption Guide.
"""

from __future__ import annotations

import html
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import quote, unquote, urlsplit
from xml.etree import ElementTree

import yaml
from markdown_it import MarkdownIt
from markdown_it.token import Token
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
MANIFEST_PATH = ROOT / "protocols.yaml"
ADOPTION_PATH = ROOT / "docs" / "agent-adoption-guide.md"
TEMPLATE_PATH = ROOT / "site" / "templates" / "layout.html"
ASSET_DIR = ROOT / "site" / "assets"
ASSET_FILES = (
    PurePosixPath("site.css"),
    PurePosixPath("favicon.svg"),
    PurePosixPath("social-card.png"),
)

BASE_URL = "https://agentwiki.iceaka.com/"
REPO_URL = "https://github.com/wangyuyan-agent/agent-wiki"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
REPOSITORY_README = PurePosixPath("README.md")
DOCS_INDEX = PurePosixPath("docs/README.md")
USECASES_INDEX = PurePosixPath("usecases/README.md")
SITE_DESCRIPTION = (
    "Agent-first protocols for memory, active workspace, skill lifecycle, "
    "councils, and stewardship—with explicit maturity, evidence, and "
    "conformance boundaries."
)

PLACEHOLDER_RE = re.compile(r"\{\{([a-z_]+)\}\}")
WHITESPACE_RE = re.compile(r"\s+")
TABLE_RE = re.compile(r"<table>(.*?)</table>", flags=re.DOTALL)
SENTENCE_BOUNDARY_RE = re.compile(r'''[.!?][\"'’”\)\]]*(?=\s|$)''')
NONTERMINAL_ABBREVIATIONS = frozenset(
    {
        "dr.",
        "e.g.",
        "i.e.",
        "mr.",
        "mrs.",
        "ms.",
        "prof.",
        "vs.",
    }
)
CONTEXTUAL_ABBREVIATIONS = frozenset({"etc.", "jr.", "sr."})
# Short opening lines are often source labels rather than useful search context;
# below this generic threshold, evaluate every complete sentence that fits.
MIN_CONTEXT_SENTENCE_LENGTH = 70


class BuildError(RuntimeError):
    """A source, rendering, or publication invariant was violated."""


class StrictSafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate keys, including merged keys."""


def _construct_unique_mapping(
    loader: StrictSafeLoader, node: MappingNode, deep: bool = False
) -> dict[Any, Any]:
    if not isinstance(node, MappingNode):
        raise ConstructorError(
            None,
            None,
            f"expected a mapping node, found {node.id}",
            node.start_mark,
        )
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            already_present = key in mapping
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from exc
        if already_present:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


@dataclass(frozen=True)
class AdoptionRoute:
    problem: str
    label: str
    href: str
    minimum: str
    first_action: str


@dataclass(frozen=True)
class DocumentMeta:
    title: str
    description: str
    kind: str
    version: str | None = None


@dataclass
class HtmlInspection:
    h1_count: int
    ids: set[str]
    duplicate_ids: set[str]
    hrefs: list[str]
    anchor_hrefs: list[str]
    canonicals: list[str]
    describedby: list[str]
    markdown_alternates: list[str]
    descriptions: list[str]
    open_graph_descriptions: list[str]
    twitter_descriptions: list[str]
    glance_protocols: list[tuple[str, str, str, str]]
    glance_problem_texts: list[str]
    glance_minimum_texts: list[str]
    glance_start_hrefs: list[str]
    glance_maturity_texts: list[str]
    glance_usecases: list[tuple[str, str, str, str]]
    glance_usecase_labels: list[str]
    glance_evidence_texts: list[str]
    glance_conformance_texts: list[str]
    protocol_backlinks: list[tuple[str, str]]
    structured_descriptions: list[str]


class PageInspector(HTMLParser):
    """Collect the small set of structural facts used by the verifier."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.h1_count = 0
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.hrefs: list[str] = []
        self.anchor_hrefs: list[str] = []
        self.canonicals: list[str] = []
        self.describedby: list[str] = []
        self.markdown_alternates: list[str] = []
        self.descriptions: list[str] = []
        self.open_graph_descriptions: list[str] = []
        self.twitter_descriptions: list[str] = []
        self.glance_protocols: list[tuple[str, str, str, str]] = []
        self.glance_problem_texts: list[str] = []
        self.glance_minimum_texts: list[str] = []
        self.glance_start_hrefs: list[str] = []
        self.glance_maturity_texts: list[str] = []
        self.glance_usecases: list[tuple[str, str, str, str]] = []
        self.glance_usecase_labels: list[str] = []
        self.glance_evidence_texts: list[str] = []
        self.glance_conformance_texts: list[str] = []
        self.protocol_backlinks: list[tuple[str, str]] = []
        self.structured_descriptions: list[str] = []
        self._text_captures: list[tuple[str, str, list[str]]] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "h1":
            self.h1_count += 1
        identifier = values.get("id")
        if identifier:
            if identifier in self.ids:
                self.duplicate_ids.add(identifier)
            self.ids.add(identifier)
        href = values.get("href")
        if href:
            self.hrefs.append(href)
            if tag == "a":
                self.anchor_hrefs.append(href)
        if tag == "meta":
            name = values.get("name", "").lower()
            property_name = values.get("property", "").lower()
            content = values.get("content", "")
            if name == "description":
                self.descriptions.append(content)
            elif property_name == "og:description":
                self.open_graph_descriptions.append(content)
            elif name == "twitter:description":
                self.twitter_descriptions.append(content)
        if tag == "aside" and "doc-glance" in values.get("class", "").split():
            self.glance_protocols.append(
                (
                    values.get("data-protocol-id", ""),
                    values.get("data-maturity", ""),
                    values.get("data-usecase-count", ""),
                    values.get("data-problem-count", ""),
                )
            )
        if tag == "a" and values.get("data-usecase-id"):
            self.glance_usecases.append(
                (
                    values["data-usecase-id"],
                    values.get("data-evidence", ""),
                    values.get("data-conformance", ""),
                    href or "",
                )
            )
        role = values.get("data-visible-role", "")
        if role:
            self._text_captures.append((tag, role, []))
            if role == "minimum" and href:
                self.glance_start_hrefs.append(href)
        if tag == "script" and values.get("type", "").lower() == "application/ld+json":
            self._text_captures.append((tag, "structured-data", []))
        if tag == "a" and values.get("data-parent-protocol-id"):
            self.protocol_backlinks.append(
                (values["data-parent-protocol-id"], href or "")
            )
        if tag != "link" or not href:
            return
        rels = set(values.get("rel", "").lower().split())
        if "canonical" in rels:
            self.canonicals.append(href)
        if "describedby" in rels:
            self.describedby.append(href)
        if "alternate" in rels and values.get("type", "").lower() == "text/markdown":
            self.markdown_alternates.append(href)

    def handle_data(self, data: str) -> None:
        for _, _, pieces in self._text_captures:
            pieces.append(data)

    def handle_endtag(self, tag: str) -> None:
        matching = [
            index for index, (capture_tag, _, _) in enumerate(self._text_captures)
            if capture_tag == tag
        ]
        if not matching:
            return
        capture_tag, role, pieces = self._text_captures.pop(matching[-1])
        if capture_tag != tag:
            return
        value = WHITESPACE_RE.sub(" ", "".join(pieces)).strip()
        destinations = {
            "problem": self.glance_problem_texts,
            "minimum": self.glance_minimum_texts,
            "maturity": self.glance_maturity_texts,
            "usecase-label": self.glance_usecase_labels,
            "evidence": self.glance_evidence_texts,
            "conformance": self.glance_conformance_texts,
        }
        if role in destinations:
            destinations[role].append(value)
        elif role == "structured-data":
            try:
                structured = json.loads("".join(pieces))
            except json.JSONDecodeError as exc:
                raise BuildError(f"invalid JSON-LD in generated page: {exc}") from exc
            if isinstance(structured, dict) and "description" in structured:
                self.structured_descriptions.append(str(structured["description"]))

    def result(self) -> HtmlInspection:
        return HtmlInspection(
            h1_count=self.h1_count,
            ids=self.ids,
            duplicate_ids=self.duplicate_ids,
            hrefs=self.hrefs,
            anchor_hrefs=self.anchor_hrefs,
            canonicals=self.canonicals,
            describedby=self.describedby,
            markdown_alternates=self.markdown_alternates,
            descriptions=self.descriptions,
            open_graph_descriptions=self.open_graph_descriptions,
            twitter_descriptions=self.twitter_descriptions,
            glance_protocols=self.glance_protocols,
            glance_problem_texts=self.glance_problem_texts,
            glance_minimum_texts=self.glance_minimum_texts,
            glance_start_hrefs=self.glance_start_hrefs,
            glance_maturity_texts=self.glance_maturity_texts,
            glance_usecases=self.glance_usecases,
            glance_usecase_labels=self.glance_usecase_labels,
            glance_evidence_texts=self.glance_evidence_texts,
            glance_conformance_texts=self.glance_conformance_texts,
            protocol_backlinks=self.protocol_backlinks,
            structured_descriptions=self.structured_descriptions,
        )


class GitHubSlugger:
    """A dependency-free approximation of GitHub's heading slug algorithm.

    The repository's headings use the GitHub-compatible subset: Unicode text,
    ASCII punctuation, inline code, and numeric section prefixes.  Punctuation
    is removed, whitespace becomes hyphens, and duplicate slugs receive the
    same ``-1``, ``-2`` suffixes used by GitHub.
    """

    def __init__(self) -> None:
        self.seen: Counter[str] = Counter()

    def slug(self, value: str) -> str:
        value = html.unescape(value).strip().lower()
        kept: list[str] = []
        for character in value:
            if character in {"-", "_"}:
                kept.append(character)
                continue
            category = unicodedata.category(character)
            if category.startswith("P") or category.startswith("C"):
                continue
            # GitHub removes ASCII mathematical/currency symbols such as + and
            # $, while allowing ordinary Unicode letters and numbers.
            if ord(character) < 128 and category.startswith("S"):
                continue
            kept.append(character)
        base = "".join(kept).replace(" ", "-")
        base = re.sub(r"[\t\n\r\f\v]", "-", base)
        if not base:
            base = "section"
        occurrence = self.seen[base]
        self.seen[base] += 1
        return base if occurrence == 0 else f"{base}-{occurrence}"


def fail(message: str) -> None:
    raise BuildError(message)


def as_mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        fail(f"{context} must be a mapping")
    return value


def as_list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{context} must be a list")
    return value


def as_string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{context} must be a non-empty string")
    return value


def safe_relative_path(value: str, context: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        fail(f"{context} is not a safe repository-relative path: {value!r}")
    return path


def output_path(relative: PurePosixPath | str) -> Path:
    relative = PurePosixPath(relative)
    if relative.is_absolute() or ".." in relative.parts:
        fail(f"unsafe output path: {relative}")
    destination = OUT.joinpath(*relative.parts)
    try:
        destination.resolve().relative_to(OUT.resolve())
    except ValueError as exc:
        raise BuildError(f"output path escapes _site: {relative}") from exc
    return destination


def write_text(relative: PurePosixPath | str, value: str) -> None:
    destination = output_path(relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(value, encoding="utf-8")


def write_bytes(relative: PurePosixPath | str, value: bytes) -> None:
    destination = output_path(relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(value)


def load_manifest() -> dict[str, Any]:
    try:
        manifest = yaml.load(
            MANIFEST_PATH.read_text(encoding="utf-8"), Loader=StrictSafeLoader
        )
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise BuildError(f"cannot load protocols.yaml strictly: {exc}") from exc
    manifest = dict(as_mapping(manifest, "protocols.yaml"))
    for key in (
        "updated",
        "maturity_vocabulary",
        "evidence_vocabulary",
        "conformance_vocabulary",
        "protocols",
        "guides",
    ):
        if key not in manifest:
            fail(f"protocols.yaml is missing required key {key!r}")
    as_string(manifest["updated"], "protocols.yaml.updated")
    for key in ("maturity_vocabulary", "evidence_vocabulary", "conformance_vocabulary"):
        vocabulary = as_mapping(manifest[key], f"protocols.yaml.{key}")
        for token, definition in vocabulary.items():
            as_string(token, f"protocols.yaml.{key} token")
            as_string(definition, f"protocols.yaml.{key}.{token}")
    protocols = as_list(manifest["protocols"], "protocols.yaml.protocols")
    guides = as_list(manifest["guides"], "protocols.yaml.guides")
    protocol_ids: set[str] = set()
    declared_documents: set[PurePosixPath] = set()
    usecase_ids: set[str] = set()
    for index, item in enumerate(protocols):
        protocol = as_mapping(item, f"protocols[{index}]")
        for key in ("id", "name", "version", "maturity", "document", "minimal_level"):
            as_string(protocol.get(key), f"protocols[{index}].{key}")
        protocol_id = protocol["id"]
        if protocol_id in protocol_ids:
            fail(f"duplicate protocol id: {protocol_id}")
        protocol_ids.add(protocol_id)
        document = safe_relative_path(protocol["document"], f"protocol {protocol_id} document")
        if document in declared_documents:
            fail(f"document declared more than once: {document}")
        declared_documents.add(document)
        if protocol["maturity"] not in manifest["maturity_vocabulary"]:
            fail(f"protocol {protocol_id} uses unknown maturity {protocol['maturity']!r}")
        for case_index, case_value in enumerate(
            as_list(protocol.get("usecases"), f"protocol {protocol_id}.usecases")
        ):
            case = as_mapping(case_value, f"protocol {protocol_id}.usecases[{case_index}]")
            for key in ("id", "evidence", "conformance", "document"):
                as_string(case.get(key), f"usecase {protocol_id}[{case_index}].{key}")
            if case["id"] in usecase_ids:
                fail(f"duplicate usecase id: {case['id']}")
            usecase_ids.add(case["id"])
            if case["evidence"] not in manifest["evidence_vocabulary"]:
                fail(f"usecase {case['id']} uses unknown evidence {case['evidence']!r}")
            if case["conformance"] not in manifest["conformance_vocabulary"]:
                fail(
                    f"usecase {case['id']} uses unknown conformance "
                    f"{case['conformance']!r}"
                )
            case_document = safe_relative_path(
                case["document"], f"usecase {case['id']} document"
            )
            if case_document in declared_documents:
                fail(f"document declared more than once: {case_document}")
            declared_documents.add(case_document)
    guide_ids: set[str] = set()
    for index, item in enumerate(guides):
        guide = as_mapping(item, f"guides[{index}]")
        for key in ("id", "version", "maturity", "document", "read_when"):
            as_string(guide.get(key), f"guides[{index}].{key}")
        if guide["id"] in guide_ids:
            fail(f"duplicate guide id: {guide['id']}")
        guide_ids.add(guide["id"])
        document = safe_relative_path(guide["document"], f"guide {guide['id']} document")
        if document in declared_documents:
            fail(f"document declared more than once: {document}")
        declared_documents.add(document)
        if guide["maturity"] not in manifest["maturity_vocabulary"]:
            fail(f"guide {guide['id']} uses unknown maturity {guide['maturity']!r}")
    for document in sorted(declared_documents):
        if not ROOT.joinpath(*document.parts).is_file():
            fail(f"manifest-declared document does not exist: {document}")
    return manifest


def discover_source_markdown() -> list[PurePosixPath]:
    paths: list[PurePosixPath] = []
    candidates = [ROOT / "README.md", *ROOT.joinpath("docs").rglob("*.md")]
    candidates.extend(ROOT.joinpath("usecases").rglob("*.md"))
    for path in candidates:
        relative = path.relative_to(ROOT)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if path.is_symlink():
            fail(f"source Markdown must not be a symlink: {relative.as_posix()}")
        if path.is_file():
            paths.append(PurePosixPath(relative.as_posix()))
    if PurePosixPath("README.md") not in paths:
        fail("README.md was not discovered")
    return sorted(set(paths), key=lambda item: item.as_posix())


def inline_plain_text(token: Token) -> str:
    children = token.children or []
    pieces: list[str] = []
    for child in children:
        if child.type in {"text", "code_inline", "html_inline"}:
            pieces.append(child.content)
        elif child.type in {"softbreak", "hardbreak"}:
            pieces.append(" ")
        elif child.type == "image":
            pieces.append(child.content)
    if not children:
        return token.content
    return WHITESPACE_RE.sub(" ", "".join(pieces)).strip()


def first_link(token: Token) -> str | None:
    for child in token.children or []:
        if child.type == "link_open":
            return child.attrGet("href")
    return None


def extract_adoption_routes(markdown: str, parser: MarkdownIt) -> list[AdoptionRoute]:
    tokens = parser.parse(markdown)
    table_start: int | None = None
    selected_section = False
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h2":
            heading = inline_plain_text(tokens[index + 1])
            selected_section = heading.startswith("3. Select by problem")
        elif selected_section and token.type == "table_open":
            table_start = index
            break
    if table_start is None:
        fail("Agent Adoption Guide has no problem-routing table in section 3")

    rows: list[list[tuple[str, str | None]]] = []
    current_row: list[tuple[str, str | None]] | None = None
    in_cell = False
    for token in tokens[table_start:]:
        if token.type == "table_close":
            break
        if token.type == "tr_open":
            current_row = []
        elif token.type == "tr_close":
            if current_row is not None:
                rows.append(current_row)
            current_row = None
        elif token.type in {"th_open", "td_open"}:
            in_cell = True
        elif token.type in {"th_close", "td_close"}:
            in_cell = False
        elif token.type == "inline" and in_cell and current_row is not None:
            current_row.append((inline_plain_text(token), first_link(token)))

    expected_header = ["Current problem", "Start with", "Minimum level", "First artifact/action"]
    if not rows or [cell[0] for cell in rows[0]] != expected_header:
        fail("Agent Adoption Guide problem table header changed unexpectedly")
    routes: list[AdoptionRoute] = []
    for row_number, row in enumerate(rows[1:], start=1):
        if len(row) != 4:
            fail(f"problem-routing row {row_number} has {len(row)} cells, expected 4")
        href = row[1][1]
        if not href:
            fail(f"problem-routing row {row_number} Start with cell has no link")
        routes.append(
            AdoptionRoute(
                problem=row[0][0],
                label=row[1][0],
                href=href,
                minimum=row[2][0],
                first_action=row[3][0],
            )
        )
    if not routes:
        fail("Agent Adoption Guide problem-routing table has no rows")
    return routes


def extract_adoption_steps(markdown: str, parser: MarkdownIt) -> list[str]:
    tokens = parser.parse(markdown)
    selected_section = False
    inside_list = False
    inside_item = False
    steps: list[str] = []
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h2":
            heading = inline_plain_text(tokens[index + 1])
            if selected_section and not heading.startswith("2. Five-step"):
                break
            selected_section = heading.startswith("2. Five-step")
        elif selected_section and token.type == "ordered_list_open":
            inside_list = True
        elif inside_list and token.type == "ordered_list_close":
            break
        elif inside_list and token.type == "list_item_open":
            inside_item = True
        elif inside_list and token.type == "list_item_close":
            inside_item = False
        elif inside_item and token.type == "inline":
            steps.append(inline_plain_text(token))
    if len(steps) != 5:
        fail(f"Agent Adoption Guide reading path must contain 5 steps, found {len(steps)}")
    return steps


def extract_minimal_binding_anchors(
    markdown: str,
    parser: MarkdownIt,
) -> dict[str, str]:
    """Map each section-4 protocol label to its generated Adoption Guide anchor."""
    tokens = parser.parse(markdown)
    add_heading_ids(tokens)
    in_minimal_bindings = False
    anchors: dict[str, str] = {}
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h2":
            heading = inline_plain_text(tokens[index + 1])
            if in_minimal_bindings:
                break
            in_minimal_bindings = heading.startswith("4. Minimal bindings")
            continue
        if in_minimal_bindings and token.type == "heading_open" and token.tag == "h3":
            heading = inline_plain_text(tokens[index + 1])
            match = re.match(r"^4\.\d+\s+(.+)$", heading)
            anchor = token.attrGet("id")
            if not match or not anchor:
                fail(f"Agent Adoption Guide has an invalid minimal-binding heading: {heading!r}")
            label = match.group(1)
            if label in anchors:
                fail(f"Agent Adoption Guide repeats minimal-binding label {label!r}")
            anchors[label] = BASE_URL + "docs/agent-adoption-guide.html#" + quote(
                anchor, safe="-._~"
            )
    if not anchors:
        fail("Agent Adoption Guide has no section-4 minimal-binding anchors")
    return anchors


def resolved_repo_path(source: PurePosixPath, href: str) -> tuple[PurePosixPath, str]:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc:
        fail(f"expected a repository-relative link, got {href!r}")
    path = parsed.path
    if not path:
        return source, parsed.fragment
    resolved = posixpath.normpath(posixpath.join(source.parent.as_posix(), path))
    if resolved == ".." or resolved.startswith("../") or resolved.startswith("/"):
        fail(f"link escapes the repository: {source} -> {href}")
    return PurePosixPath(resolved), parsed.fragment


def html_url_for_markdown(relative: PurePosixPath) -> str:
    return BASE_URL + quote(relative.with_suffix(".html").as_posix(), safe="/-._~")


def source_url(relative: PurePosixPath) -> str:
    return BASE_URL + quote(relative.as_posix(), safe="/-._~")


def repo_blob_url(relative: PurePosixPath, revision: str) -> str:
    return f"{REPO_URL}/blob/{quote(revision, safe='')}/{quote(relative.as_posix(), safe='/-._~')}"


def landing_href_for_adoption_link(href: str) -> str:
    target, fragment = resolved_repo_path(PurePosixPath("docs/agent-adoption-guide.md"), href)
    if target.suffix.lower() == ".md":
        target = target.with_suffix(".html")
    url = BASE_URL + quote(target.as_posix(), safe="/-._~")
    return f"{url}#{quote(fragment, safe='-._~')}" if fragment else url


def rewrite_markdown_href(href: str) -> str:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return href
    path = parsed.path
    if path.lower().endswith(".md"):
        path = path[:-3] + ".html"
    rebuilt = path
    if parsed.query:
        rebuilt += f"?{parsed.query}"
    if parsed.fragment:
        rebuilt += f"#{parsed.fragment}"
    return rebuilt


def make_markdown_parser() -> MarkdownIt:
    parser = MarkdownIt(
        "commonmark",
        {
            "html": False,
            "linkify": False,
            "typographer": False,
        },
    ).enable("table")
    default_link_open = parser.renderer.rules.get("link_open")

    def render_link_open(
        renderer: Any,
        tokens: Sequence[Token],
        index: int,
        options: Mapping[str, Any],
        env: Mapping[str, Any],
    ) -> str:
        href = tokens[index].attrGet("href")
        if href:
            tokens[index].attrSet("href", rewrite_markdown_href(href))
        if default_link_open:
            return default_link_open(tokens, index, options, env)
        return renderer.renderToken(tokens, index, options, env)

    parser.add_render_rule("link_open", render_link_open)
    return parser


def add_heading_ids(tokens: Sequence[Token]) -> None:
    slugger = GitHubSlugger()
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        if index + 1 >= len(tokens) or tokens[index + 1].type != "inline":
            fail("Markdown heading is missing its inline token")
        heading = inline_plain_text(tokens[index + 1])
        token.attrSet("id", slugger.slug(heading))


def markdown_title_and_description(tokens: Sequence[Token]) -> tuple[str, str]:
    title = ""
    paragraphs: list[str] = []
    list_depth = 0
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h1" and not title:
            title = inline_plain_text(tokens[index + 1])
        if token.type in {"bullet_list_open", "ordered_list_open"}:
            list_depth += 1
        elif token.type in {"bullet_list_close", "ordered_list_close"}:
            list_depth = max(0, list_depth - 1)
        elif token.type == "paragraph_open" and list_depth == 0 and index + 1 < len(tokens):
            candidate = inline_plain_text(tokens[index + 1])
            if candidate:
                paragraphs.append(WHITESPACE_RE.sub(" ", candidate).strip())
    if not title:
        fail("Markdown document has no H1")
    description = ""
    for paragraph in paragraphs:
        remainder = paragraph
        while remainder:
            candidate = first_sentence(remainder)
            if is_complete_sentence(candidate) and 40 <= len(candidate) <= 157:
                description = candidate
                break
            if candidate == remainder:
                break
            remainder = remainder[len(candidate):].lstrip()
        if description:
            break
    if not description:
        fail(f"Markdown document {title!r} has no complete 40..157 character description")
    return title, description


def first_sentence_end(value: str) -> int | None:
    for match in SENTENCE_BOUNDARY_RE.finditer(value):
        candidate = value[: match.end()]
        without_closers = re.sub(r'''[\"'’”\)\]]+$''', "", candidate)
        last_token = without_closers.rsplit(" ", 1)[-1].lower().lstrip("([{\"'‘“")
        remainder = value[match.end():].lstrip()
        if not remainder:
            return match.end()
        if last_token in NONTERMINAL_ABBREVIATIONS:
            continue
        # An initialism or contextual abbreviation followed by more prose is
        # ambiguous without a language model ("U.S. Kiro runtime" versus
        # "U.S. Next sentence"). Keep scanning instead of risking a fragment;
        # returning two complete sentences is safer than returning half of one.
        if last_token in CONTEXTUAL_ABBREVIATIONS or re.fullmatch(
            r"(?:[a-z]\.){2,}", last_token
        ):
            continue
        return match.end()
    return None


def first_sentence(value: str) -> str:
    value = WHITESPACE_RE.sub(" ", value).strip()
    sentence_end = first_sentence_end(value)
    if sentence_end is not None:
        return value[:sentence_end]
    return value


def is_complete_sentence(value: str) -> bool:
    value = WHITESPACE_RE.sub(" ", value).strip()
    return bool(value) and first_sentence_end(value) == len(value)


def section_one_sentences(
    source: str,
    parser: MarkdownIt,
    context: str,
    *,
    require_purpose: bool = False,
) -> list[str]:
    """Extract complete prose sentences from section 1, excluding list metadata."""
    tokens = parser.parse(source)
    in_section_one = False
    list_depth = 0
    heading = ""
    sentences: list[str] = []
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h2":
            heading = inline_plain_text(tokens[index + 1])
            if in_section_one:
                break
            in_section_one = bool(re.match(r"^1\.\s+", heading))
            if in_section_one and require_purpose and not heading.startswith("1. Purpose"):
                fail(f"{context} section 1 must be Purpose, found {heading!r}")
            continue
        if token.type in {"bullet_list_open", "ordered_list_open"}:
            list_depth += 1
            continue
        if token.type in {"bullet_list_close", "ordered_list_close"}:
            list_depth = max(0, list_depth - 1)
            continue
        if (
            in_section_one
            and list_depth == 0
            and token.type == "paragraph_open"
            and index + 1 < len(tokens)
        ):
            paragraph = WHITESPACE_RE.sub(" ", inline_plain_text(tokens[index + 1])).strip()
            while paragraph:
                sentence = first_sentence(paragraph)
                if (
                    sentence
                    and is_complete_sentence(sentence)
                    and (not require_purpose or not sentence.endswith(":"))
                ):
                    sentences.append(sentence)
                if sentence == paragraph:
                    break
                paragraph = paragraph[len(sentence):].lstrip()
    if not sentences:
        fail(f"{context} has no prose sentence in section 1")
    return sentences


def extract_section_one_sentence(
    source: str,
    parser: MarkdownIt,
    context: str,
    *,
    require_purpose: bool = False,
) -> str:
    return section_one_sentences(
        source,
        parser,
        context,
        require_purpose=require_purpose,
    )[0]


def select_protocol_purpose(
    source: str,
    parser: MarkdownIt,
    protocol: Mapping[str, Any],
) -> str:
    """Select the strongest source sentence without maintaining separate SEO copy."""
    sentences = section_one_sentences(
        source,
        parser,
        f"protocol {protocol['id']}",
        require_purpose=True,
    )
    short_name = str(protocol["name"]).removeprefix("Agent-first ")
    direct_name = re.compile(rf"\b(?:a|an|the)?\s*{re.escape(short_name)}\s+is\b", re.I)

    product_sentences = [
        sentence
        for sentence in sentences
        if re.search(r"\b(?:the|its) product\b.{0,55}\bis\b", sentence, re.I)
    ]
    if product_sentences:
        return product_sentences[0]
    direct_definitions = [sentence for sentence in sentences if direct_name.search(sentence)]
    if direct_definitions:
        return direct_definitions[0]
    return sentences[0]


def select_usecase_context(
    source: str,
    parser: MarkdownIt,
    case: Mapping[str, Any],
    max_length: int,
) -> str:
    """Select a complete, source-derived case sentence that fits before its suffix."""
    sentences = section_one_sentences(source, parser, f"usecase {case['id']}")
    opening = sentences[0]
    if (
        len(opening) >= MIN_CONTEXT_SENTENCE_LENGTH
        and len(opening) <= max_length
        and is_complete_sentence(opening)
    ):
        return opening

    tokens = parser.parse(source)
    title = ""
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h1":
            title = inline_plain_text(tokens[index + 1])
            break
    if not title:
        fail(f"usecase {case['id']} has no H1 for description fallback")
    title_sentence = title.rstrip(" .!?") + "."

    complete = [
        (index, sentence)
        for index, sentence in enumerate(sentences)
        if len(sentence) <= max_length
        and is_complete_sentence(sentence)
    ]
    if complete:
        # Prefer the most informative sentence that fits the fixed suffix budget;
        # preserve source order when two candidates have the same length.
        context = max(complete, key=lambda item: (len(item[1]), -item[0]))[1]
        contextualized = f"{title} — {context}"
        if len(contextualized) <= max_length:
            return contextualized
        return context
    if len(title_sentence) <= max_length:
        return title_sentence
    fail(f"usecase {case['id']} has no complete source-derived description within budget")


def verify_text_extractors(parser: MarkdownIt) -> None:
    """Guard the punctuation and list boundaries used by generated descriptions."""
    quoted = 'It is complete.” Next sentence.'
    if first_sentence(quoted) != 'It is complete.”':
        fail("sentence extraction must retain closing quotation marks")
    abbreviation_cases = {
        "This use case uses e.g. examples. Next sentence.": "This use case uses e.g. examples.",
        "This ran on the U.S. runtime. Next sentence.": "This ran on the U.S. runtime.",
        "This ran on the U.S. Next sentence.": "This ran on the U.S. Next sentence.",
        "This ran on the U.S. Kiro runtime. Next sentence.": "This ran on the U.S. Kiro runtime.",
        "The U.S. Department published it. Next sentence.": "The U.S. Department published it.",
        "This ran in the U.S. “runtime profile” mode. Next sentence.": "This ran in the U.S. “runtime profile” mode.",
        "Dr. Smith reviewed it. Next sentence.": "Dr. Smith reviewed it.",
        "Use examples (e.g. local cache). Next sentence.": "Use examples (e.g. local cache).",
        "Use examples (e.g. Local cache). Next sentence.": "Use examples (e.g. Local cache).",
        "Use examples, etc. Next sentence.": "Use examples, etc. Next sentence.",
    }
    for value, expected in abbreviation_cases.items():
        if first_sentence(value) != expected:
            fail(f"sentence extraction split an abbreviation in {value!r}")
    if is_complete_sentence("This paragraph has no terminal punctuation"):
        fail("sentence extraction accepted prose without terminal punctuation")
    if is_complete_sentence("This paragraph uses e.g. examples without a terminator"):
        fail("sentence extraction mistook an abbreviation for terminal punctuation")
    if not is_complete_sentence("This ran on the U.S."):
        fail("sentence extraction rejected a sentence ending in an initialism")
    sample = """# Synthetic\n\n## 1. Context\n\n- Metadata-like first list item.\n\nActual prose sentence. Follow-up.\n\n## 2. Boundary\n"""
    extracted = section_one_sentences(sample, parser, "synthetic extraction check")
    if extracted != ["Actual prose sentence.", "Follow-up."]:
        fail("section-1 extraction must ignore list items and preserve prose sentences")
    incomplete = parser.parse(
        "# Synthetic\n\n"
        "This deliberately long source fragment has enough characters for metadata "
        "but no terminal punctuation"
    )
    try:
        markdown_title_and_description(incomplete)
    except BuildError:
        pass
    else:
        fail("generic Markdown descriptions must fail closed on incomplete prose")
    incomplete_section = (
        "# Synthetic\n\n"
        "## 1. Purpose\n\n"
        "This deliberately long purpose paragraph has no terminal punctuation\n\n"
        "## 2. Boundary\n\n"
        "A complete sentence outside the selected section.\n"
    )
    try:
        section_one_sentences(
            incomplete_section,
            parser,
            "synthetic incomplete-purpose check",
            require_purpose=True,
        )
    except BuildError:
        pass
    else:
        fail("section-1 descriptions must fail closed on incomplete prose")


def truncate_description(value: str, suffix: str = "") -> str:
    """Fit a snippet to 157 characters without cutting a Latin word or suffix."""
    value = WHITESPACE_RE.sub(" ", value).strip()
    suffix = WHITESPACE_RE.sub(" ", suffix).strip()
    combined = f"{value} {suffix}".strip()
    if len(combined) <= 157:
        return combined

    prefix_limit = 157 if not suffix else 156 - len(suffix)
    if prefix_limit < 2:
        fail("description suffix leaves no room for a meaningful prefix")
    candidate = value[: prefix_limit - 1].rstrip(" ,;:-")
    if len(value) > len(candidate):
        boundary = candidate.rfind(" ")
        if boundary > 0:
            candidate = candidate[:boundary].rstrip(" ,;:-")
        candidate += "…"
    return f"{candidate} {suffix}".strip()


def render_markdown_document(
    relative: PurePosixPath,
    source: str,
    parser: MarkdownIt,
) -> tuple[str, str, str]:
    tokens = parser.parse(source, {"source": relative.as_posix()})
    add_heading_ids(tokens)
    title, description = markdown_title_and_description(tokens)
    rendered = parser.renderer.render(tokens, parser.options, {"source": relative.as_posix()})
    rendered = TABLE_RE.sub(r'<div class="table-scroll"><table>\1</table></div>', rendered)
    return title, description, rendered


def render_template(template: str, values: Mapping[str, str]) -> str:
    missing = set(PLACEHOLDER_RE.findall(template)) - set(values)
    if missing:
        fail(f"layout template values are missing: {', '.join(sorted(missing))}")

    def replacement(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            fail(f"unknown layout placeholder: {key}")
        return values[key]

    # ``re.sub`` scans the template only once, so brace-shaped examples inside
    # rendered source documents are preserved and are not mistaken for layout
    # placeholders.
    return PLACEHOLDER_RE.sub(replacement, template)


def json_for_script(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def navigation() -> str:
    return (
        '<div class="nav-links">'
        f'<a href="{BASE_URL}#protocols">Protocols</a>'
        f'<a href="{BASE_URL}#evidence">Evidence</a>'
        f'<a href="{BASE_URL}docs/agent-adoption-guide.html">Adopt</a>'
        f'<a href="{BASE_URL}llms.txt">For Agents</a>'
        f'<a class="external-link" href="{REPO_URL}">GitHub</a>'
        "</div>"
    )


def footer(revision: str) -> str:
    revision_link = f"{REPO_URL}/tree/{quote(revision, safe='')}"
    return f"""
<footer class="site-footer">
  <div class="shell footer-inner">
    <p class="footer-authority"><strong>Authority stays with the source.</strong> <code>protocols.yaml</code> is the routing and vocabulary authority; each protocol document is authoritative for its own semantics. This website is a generated reading surface.</p>
    <div class="footer-meta">
      <div class="footer-links">
        <a href="{html_url_for_markdown(REPOSITORY_README)}">Project README</a>
        <a href="{BASE_URL}index.md">Markdown index</a>
        <a href="{BASE_URL}llms.txt">llms.txt</a>
        <a href="{BASE_URL}sitemap.xml">Sitemap</a>
        <a class="external-link" href="{REPO_URL}">Repository</a>
      </div>
      <a class="revision" href="{revision_link}">source {html.escape(revision[:12])}</a>
    </div>
  </div>
</footer>""".strip()


def page_values(
    *,
    title: str,
    description: str,
    canonical: str,
    markdown_alternate: str,
    main: str,
    main_class: str,
    body_class: str,
    structured_data: Mapping[str, Any],
    revision: str,
    asset_prefix: str = "",
    robots: str = "",
    include_footer: bool = True,
) -> dict[str, str]:
    safe_title = html.escape(title)
    safe_description = html.escape(description, quote=True)
    nav = navigation()
    return {
        "title": safe_title,
        "description": safe_description,
        "robots_meta": robots,
        "canonical_link": f'<link rel="canonical" href="{html.escape(canonical, quote=True)}">',
        "alternate_link": (
            '<link rel="alternate" type="text/markdown" '
            f'href="{html.escape(markdown_alternate, quote=True)}">'
        ),
        "describedby_href": BASE_URL + "llms.txt",
        "asset_prefix": asset_prefix,
        "og_url": html.escape(canonical, quote=True),
        "og_image": BASE_URL + "assets/social-card.png",
        "structured_data": json_for_script(structured_data),
        "body_class": body_class,
        "home_href": BASE_URL,
        "desktop_nav": nav,
        "mobile_nav": nav,
        "main_class": main_class,
        "main": main,
        "footer": footer(revision) if include_footer else "",
    }


def manifest_collections(
    manifest: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    protocols = [as_mapping(item, "protocol") for item in as_list(manifest["protocols"], "protocols")]
    guides = [as_mapping(item, "guide") for item in as_list(manifest["guides"], "guides")]
    usecases: list[Mapping[str, Any]] = []
    for protocol in protocols:
        for item in as_list(protocol["usecases"], f"{protocol['id']}.usecases"):
            case = dict(as_mapping(item, "usecase"))
            case["protocol_id"] = protocol["id"]
            usecases.append(case)
    return protocols, guides, usecases


def routes_by_document(
    routes: Sequence[AdoptionRoute],
) -> dict[PurePosixPath, list[AdoptionRoute]]:
    grouped: dict[PurePosixPath, list[AdoptionRoute]] = {}
    for route in routes:
        grouped.setdefault(route_target_document(route), []).append(route)
    return grouped


def document_metadata(
    manifest: Mapping[str, Any],
    routes: Sequence[AdoptionRoute],
    source_texts: Mapping[PurePosixPath, str],
    parser: MarkdownIt,
) -> dict[PurePosixPath, DocumentMeta]:
    protocols, guides, usecases = manifest_collections(manifest)
    route_groups = routes_by_document(routes)
    metadata: dict[PurePosixPath, DocumentMeta] = {}
    for protocol in protocols:
        document = PurePosixPath(str(protocol["document"]))
        document_routes = route_groups.get(document, [])
        if not document_routes:
            fail(f"protocol {protocol['id']} has no Agent Adoption Guide problem route")
        for route in document_routes:
            if route.minimum != protocol["minimal_level"]:
                fail(
                    f"protocol {protocol['id']} route minimum {route.minimum!r} does not "
                    f"match manifest minimal_level {protocol['minimal_level']!r}"
                )
        source = source_texts.get(document)
        if source is None:
            fail(f"protocol source was not loaded: {document}")
        if len(document_routes) > 1:
            description = truncate_description(" — ".join(route.problem for route in document_routes) + ".")
        else:
            purpose = select_protocol_purpose(source, parser, protocol)
            description = truncate_description(f"{document_routes[0].problem} — {purpose}")
        metadata[document] = DocumentMeta(
            title=protocol["name"],
            description=description,
            kind="protocol",
            version=protocol["version"],
        )
    for guide in guides:
        document = PurePosixPath(str(guide["document"]))
        read_when = str(guide["read_when"]).strip()
        description = f"{guide['maturity']} guide — Read when: {read_when}"
        if description[-1] not in ".!?":
            description += "."
        if len(description) > 157:
            source = source_texts.get(document)
            if source is None:
                fail(f"guide source was not loaded: {document}")
            candidates = section_one_sentences(
                source,
                parser,
                f"guide {guide['id']}",
                require_purpose=True,
            )
            contextualized = [
                f"{guide['maturity']} guide — {candidate}"
                for candidate in candidates
                if 40 <= len(f"{guide['maturity']} guide — {candidate}") <= 157
                and is_complete_sentence(candidate)
            ]
            if contextualized:
                description = contextualized[0]
            else:
                fail(
                    f"guide {guide['id']} has no complete source-derived description "
                    "that preserves maturity"
                )
        metadata[document] = DocumentMeta(
            title=f"{guide['id']} guide",
            description=description,
            kind="guide",
            version=guide["version"],
        )
    for case in usecases:
        document = PurePosixPath(str(case["document"]))
        source = source_texts.get(document)
        if source is None:
            fail(f"usecase source was not loaded: {document}")
        suffix = f"Evidence: {case['evidence']}; conformance: {case['conformance']}."
        context = select_usecase_context(
            source,
            parser,
            case,
            max_length=156 - len(suffix),
        )
        description = truncate_description(context, suffix)
        if "…" in description:
            fail(f"usecase {case['id']} description must preserve a complete source sentence")
        metadata[document] = DocumentMeta(
            title=case["id"],
            description=description,
            kind="usecase",
        )
    usecase_index_owners: dict[PurePosixPath, str] = {}
    for protocol in protocols:
        protocol_cases = [
            case
            for case in usecases
            if str(case["protocol_id"]) == str(protocol["id"])
        ]
        if not protocol_cases:
            continue
        parents = {
            PurePosixPath(str(case["document"])).parent
            for case in protocol_cases
        }
        if len(parents) != 1:
            fail(f"protocol {protocol['id']} use cases span multiple index directories")
        index_document = next(iter(parents)) / "README.md"
        owner = usecase_index_owners.get(index_document)
        if owner is not None:
            fail(
                f"use-case index {index_document} is shared by protocols "
                f"{owner} and {protocol['id']}"
            )
        usecase_index_owners[index_document] = str(protocol["id"])
        if index_document not in source_texts:
            fail(f"protocol {protocol['id']} has no use-case index at {index_document}")
        evidence = list(dict.fromkeys(str(case["evidence"]) for case in protocol_cases))
        conformance = list(
            dict.fromkeys(str(case["conformance"]) for case in protocol_cases)
        )
        count = len(protocol_cases)
        case_label = "use case" if count == 1 else "use cases"
        description = (
            f"{protocol['id']} use cases — {count} documented {case_label}; "
            f"evidence: {', '.join(evidence)}; "
            f"conformance: {', '.join(conformance)}."
        )
        if not 40 <= len(description) <= 157:
            fail(
                f"protocol {protocol['id']} use-case index description length is "
                f"{len(description)}; expected 40..157"
            )
        metadata[index_document] = DocumentMeta(
            title=f"{protocol['id']} use cases",
            description=description,
            kind="usecase-index",
        )
    return metadata


def render_protocol_glance(
    protocol: Mapping[str, Any],
    routes: Sequence[AdoptionRoute],
    manifest: Mapping[str, Any],
    adoption_minimum: str,
) -> str:
    maturity = str(protocol["maturity"])
    maturity_definition = str(manifest["maturity_vocabulary"][maturity])
    usecases = [
        as_mapping(item, f"protocol {protocol['id']}.usecases")
        for item in as_list(protocol["usecases"], f"protocol {protocol['id']}.usecases")
    ]
    if usecases:
        usecase_items: list[str] = []
        for case in usecases:
            evidence = str(case["evidence"])
            evidence_definition = str(manifest["evidence_vocabulary"][evidence])
            conformance = str(case["conformance"])
            conformance_definition = str(
                manifest["conformance_vocabulary"][conformance]
            )
            case_id = str(case["id"])
            case_url = html_url_for_markdown(PurePosixPath(str(case["document"])))
            usecase_items.append(
                "<li>"
                f'<a data-usecase-id="{html.escape(case_id, quote=True)}" '
                f'data-evidence="{html.escape(evidence, quote=True)}" '
                f'data-conformance="{html.escape(conformance, quote=True)}" '
                f'data-visible-role="usecase-label" href="{case_url}">'
                f"{html.escape(case_id)}</a>"
                '<span class="doc-glance-usecase-meta">'
                f'<abbr data-visible-role="evidence" '
                f'title="Evidence — {html.escape(evidence_definition, quote=True)}">'
                f"{html.escape(evidence)}</abbr>"
                '<span aria-hidden="true"> · </span>'
                f'<abbr data-visible-role="conformance" '
                f'title="Conformance — {html.escape(conformance_definition, quote=True)}">'
                f"{html.escape(conformance)}</abbr></span></li>"
            )
        usecase_html = f'<ul class="doc-glance-usecases">{"".join(usecase_items)}</ul>'
    else:
        usecase_html = '<span class="doc-glance-empty">None documented yet</span>'

    problem_html = '<span aria-hidden="true"> · </span>'.join(
        f'<span data-visible-role="problem">{html.escape(route.problem)}</span>'
        for route in routes
    )
    return (
        f'<aside class="doc-glance" aria-label="{html.escape(str(protocol["name"]), quote=True)} at a glance" '
        f'data-protocol-id="{html.escape(str(protocol["id"]), quote=True)}" '
        f'data-maturity="{html.escape(maturity, quote=True)}" '
        f'data-usecase-count="{len(usecases)}" '
        f'data-problem-count="{len(routes)}">'
        '<p class="doc-glance-title">At a glance</p>'
        '<dl>'
        '<div class="doc-glance-item doc-glance-problem"><dt>Problem</dt>'
        f'<dd class="doc-glance-problems">{problem_html}</dd></div>'
        '<div class="doc-glance-item"><dt>Start at</dt>'
        f'<dd><a data-visible-role="minimum" href="{adoption_minimum}">'
        f'<code>{html.escape(str(protocol["minimal_level"]))}</code></a></dd></div>'
        '<div class="doc-glance-item"><dt>Maturity</dt>'
        f'<dd><abbr data-visible-role="maturity" '
        f'title="{html.escape(maturity_definition, quote=True)}">'
        f"{html.escape(maturity)}</abbr></dd></div>"
        '<div class="doc-glance-item doc-glance-related"><dt>Use cases</dt>'
        f"<dd>{usecase_html}</dd></div>"
        "</dl></aside>"
    )


def render_source_pages(
    *,
    source_markdown: Sequence[PurePosixPath],
    source_texts: Mapping[PurePosixPath, str],
    parser: MarkdownIt,
    template: str,
    manifest: Mapping[str, Any],
    metadata: Mapping[PurePosixPath, DocumentMeta],
    routes: Sequence[AdoptionRoute],
    revision: str,
) -> list[PurePosixPath]:
    protocols, _, usecases = manifest_collections(manifest)
    protocols_by_document = {
        PurePosixPath(str(protocol["document"])): protocol for protocol in protocols
    }
    protocols_by_id = {str(protocol["id"]): protocol for protocol in protocols}
    usecases_by_document = {
        PurePosixPath(str(case["document"])): case for case in usecases
    }
    route_groups = routes_by_document(routes)
    adoption_source = source_texts.get(PurePosixPath("docs/agent-adoption-guide.md"))
    if adoption_source is None:
        fail("Agent Adoption Guide source was not loaded for minimal-binding anchors")
    minimal_anchors = extract_minimal_binding_anchors(adoption_source, parser)
    rendered_paths: list[PurePosixPath] = []
    for relative in source_markdown:
        source = source_texts[relative]
        title, extracted_description, rendered = render_markdown_document(relative, source, parser)
        declared = metadata.get(relative)
        description = truncate_description(
            declared.description if declared else extracted_description
        )
        canonical = html_url_for_markdown(relative)
        markdown_alternate = source_url(relative)
        source_links: list[str] = []
        case = usecases_by_document.get(relative)
        if case:
            parent = protocols_by_id[str(case["protocol_id"])]
            parent_id = str(parent["id"])
            parent_url = html_url_for_markdown(PurePosixPath(str(parent["document"])))
            source_links.append(
                f'Protocol: <a data-parent-protocol-id="{html.escape(parent_id, quote=True)}" '
                f'href="{parent_url}">{html.escape(str(parent["name"]))}</a>'
            )
        source_links.extend(
            (
                f'<a href="{markdown_alternate}">Markdown</a>',
                f'<a class="external-link" href="{repo_blob_url(relative, revision)}">GitHub source</a>',
            )
        )
        sourcebar = (
            '<div class="doc-sourcebar">'
            f'<span>Source · {html.escape(relative.as_posix())}</span>'
            f'<span>{" · ".join(source_links)}'
            "</span></div>"
        )
        glance = ""
        protocol = protocols_by_document.get(relative)
        if protocol:
            protocol_routes = route_groups.get(relative, [])
            if not protocol_routes:
                fail(f"protocol {protocol['id']} has no route for its At a glance block")
            route_labels = {route.label for route in protocol_routes}
            if len(route_labels) != 1:
                fail(f"protocol {protocol['id']} routes disagree on their Adoption Guide label")
            route_label = next(iter(route_labels))
            adoption_minimum = minimal_anchors.get(route_label)
            if not adoption_minimum:
                fail(
                    f"protocol {protocol['id']} has no section-4 minimal-binding anchor "
                    f"for {route_label!r}"
                )
            glance = render_protocol_glance(
                protocol,
                protocol_routes,
                manifest,
                adoption_minimum,
            )
            h1_end = rendered.find("</h1>")
            if h1_end < 0:
                fail(f"protocol {protocol['id']} rendered without an H1")
            insertion = h1_end + len("</h1>")
            rendered = rendered[:insertion] + glance + rendered[insertion:]
        main = f'<div class="doc-shell">{sourcebar}<article class="doc">{rendered}</article></div>'
        structured: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "headline": title,
            "description": description,
            "url": canonical,
            "isPartOf": {"@type": "WebSite", "name": "agent-wiki", "url": BASE_URL},
            "license": LICENSE_URL,
            "codeRepository": REPO_URL,
        }
        if declared:
            structured["articleSection"] = declared.kind
            if declared.version:
                structured["version"] = declared.version
        output_relative = relative.with_suffix(".html")
        asset_prefix = "../" * len(output_relative.parent.parts)
        values = page_values(
            title=f"{title} · agent-wiki",
            description=description,
            canonical=canonical,
            markdown_alternate=markdown_alternate,
            main=main,
            main_class="doc-main",
            body_class="source-document",
            structured_data=structured,
            revision=revision,
            asset_prefix=asset_prefix,
        )
        write_text(output_relative, render_template(template, values))
        rendered_paths.append(output_relative)
    return rendered_paths


def vocabulary_html(vocabulary: Mapping[str, str]) -> str:
    parts = []
    for token, definition in vocabulary.items():
        parts.append(
            f'<abbr title="{html.escape(definition, quote=True)}">{html.escape(token)}</abbr>'
        )
    return " · ".join(parts)


def counts_html(counts: Counter[str], vocabulary: Mapping[str, str]) -> str:
    return " · ".join(
        f"<code>{html.escape(token)} {counts.get(token, 0)}</code>" for token in vocabulary
    )


def markdown_escape_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def route_target_document(route: AdoptionRoute) -> PurePosixPath:
    target, _ = resolved_repo_path(PurePosixPath("docs/agent-adoption-guide.md"), route.href)
    return target


def render_landing(
    *,
    manifest: Mapping[str, Any],
    routes: Sequence[AdoptionRoute],
    adoption_steps: Sequence[str],
    template: str,
    revision: str,
) -> str:
    protocols, guides, usecases = manifest_collections(manifest)
    maturity_vocabulary = as_mapping(manifest["maturity_vocabulary"], "maturity vocabulary")
    evidence_vocabulary = as_mapping(manifest["evidence_vocabulary"], "evidence vocabulary")
    conformance_vocabulary = as_mapping(
        manifest["conformance_vocabulary"], "conformance vocabulary"
    )
    maturity_counts = Counter(str(item["maturity"]) for item in protocols)
    evidence_counts = Counter(str(item["evidence"]) for item in usecases)
    conformance_counts = Counter(str(item["conformance"]) for item in usecases)
    verified_count = conformance_counts.get("verified", 0)

    route_rows = []
    for route in routes:
        protocol_label = f"{route.label} · {route.minimum}"
        route_rows.append(
            "<li>"
            f'<a class="problem-link" href="{landing_href_for_adoption_link(route.href)}" '
            f'title="First action: {html.escape(route.first_action, quote=True)}">'
            f'<span class="problem-text">{html.escape(route.problem)}</span>'
            f'<span class="problem-protocol">{html.escape(protocol_label)}</span>'
            '<span class="problem-arrow" aria-hidden="true">→</span>'
            "</a></li>"
        )

    route_groups = routes_by_document(routes)

    protocol_rows = []
    for protocol in protocols:
        document = PurePosixPath(str(protocol["document"]))
        case_counts = Counter(
            str(item["conformance"])
            for item in as_list(protocol["usecases"], f"{protocol['id']}.usecases")
        )
        if case_counts:
            case_summary = " · ".join(
                f"{token} {case_counts[token]}" for token in conformance_vocabulary if case_counts[token]
            )
        else:
            case_summary = "0 documented"
        document_routes = route_groups.get(document, [])
        if not document_routes:
            fail(f"protocol {protocol['id']} has no Agent Adoption Guide problem route")
        problem = document_routes[0].problem
        maturity = str(protocol["maturity"])
        protocol_rows.append(
            "<tr>"
            '<td data-label="Protocol">'
            f'<a class="protocol-name" href="{html_url_for_markdown(document)}">'
            f"{html.escape(str(protocol['name']))}</a>"
            f'<span class="protocol-problem">{html.escape(problem)}</span>'
            "</td>"
            f'<td data-label="Version"><code>{html.escape(str(protocol["version"]))}</code></td>'
            f'<td data-label="Maturity"><abbr class="token" title="{html.escape(str(maturity_vocabulary[maturity]), quote=True)}">{html.escape(maturity)}</abbr></td>'
            f'<td data-label="Minimum"><code>{html.escape(str(protocol["minimal_level"]))}</code></td>'
            f'<td data-label="Usecase conformance"><span class="token">{html.escape(case_summary)}</span></td>'
            "</tr>"
        )

    step_titles = [
        "Read the manifest",
        "Select by problem",
        "Read the complete contract",
        "Calibrate with one use case",
        "Compose only when required",
    ]
    steps_html = "".join(
        f"<li><h3>{html.escape(title)}</h3><p>{html.escape(step)}</p></li>"
        for title, step in zip(step_titles, adoption_steps)
    )

    main = f"""
<div class="landing-content" data-protocol-count="{len(protocols)}" data-guide-count="{len(guides)}" data-usecase-count="{len(usecases)}" data-problem-count="{len(routes)}" data-verified-count="{verified_count}">
  <section class="hero">
    <div class="shell hero-grid">
      <div>
        <h1>Portable protocols for agent memory and coordination.</h1>
        <p class="hero-copy">agent-wiki is an agent-first, machine-readable knowledge base for memory, workspace, skill lifecycle, deliberation, and coordination. Start with one problem and the smallest useful binding.</p>
        <div class="hero-actions">
          <a class="button button-primary" href="{BASE_URL}protocols.yaml">Read the manifest <span class="arrow" aria-hidden="true">→</span></a>
          <a class="button" href="{BASE_URL}docs/agent-adoption-guide.html">Choose a protocol</a>
        </div>
      </div>
      <div class="route-panel" aria-label="Agent reading path">
        <p class="route-caption">Smallest reliable reading path</p>
        <div class="route-track">
          <div class="route-step"><span class="route-node" aria-hidden="true"></span><p class="route-label">01 · Route</p><p class="route-value">protocols.yaml</p></div>
          <div class="route-step"><span class="route-node" aria-hidden="true"></span><p class="route-label">02 · Bind</p><p class="route-value">one minimum level</p></div>
          <div class="route-step"><span class="route-node" aria-hidden="true"></span><p class="route-label">03 · Calibrate</p><p class="route-value">one matching use case, when available</p></div>
        </div>
      </div>
    </div>
  </section>

  <div class="fact-rail">
    <div class="shell">
      <ul class="fact-list" aria-label="Manifest snapshot">
        <li>{len(protocols)} protocols</li>
        <li><a href="{html_url_for_markdown(DOCS_INDEX)}">{len(guides)} guides</a></li>
        <li><a href="{html_url_for_markdown(USECASES_INDEX)}">{len(usecases)} documented use cases</a></li>
        <li>CC BY 4.0</li>
      </ul>
    </div>
  </div>

  <section id="routes" class="landing-section">
    <div class="shell">
      <div class="section-heading-row">
        <div><span class="section-number">01 · Route by problem</span><h2>Start with the constraint you actually have.</h2></div>
        <p class="section-intro">The Adoption Guide is the source for this routing table. Selection does not authorize environment changes, and adding a protocol is unnecessary when a simpler action already solves the problem.</p>
      </div>
      <ol class="problem-list">{''.join(route_rows)}</ol>
    </div>
  </section>

  <section id="protocols" class="landing-section">
    <div class="shell">
      <div class="section-heading-row">
        <div><span class="section-number">02 · Protocol registry</span><h2>Choose the smallest sufficient binding.</h2></div>
        <p id="protocol-table-description" class="section-intro">Levels are cumulative within one protocol and are not comparable across protocols. Versions below 1.0.0 may change incompatibly.</p>
      </div>
      <div class="protocol-table-wrap">
        <table class="protocol-table" aria-describedby="protocol-table-description">
          <thead><tr><th>Protocol</th><th>Version</th><th>Maturity</th><th>Minimum</th><th>Usecase conformance</th></tr></thead>
          <tbody>{''.join(protocol_rows)}</tbody>
        </table>
      </div>
    </div>
  </section>

  <section id="evidence" class="landing-section evidence-band">
    <div class="shell">
      <div class="section-heading-row">
        <div><span class="section-number">03 · Evidence discipline</span><h2>Three axes. No borrowed certainty.</h2></div>
        <p class="section-intro">Maturity describes the protocol, evidence describes an observation boundary, and conformance describes checks against a named protocol version. One does not silently upgrade another.</p>
      </div>
      <div class="evidence-grid">
        <div class="evidence-axis"><h3>Maturity</h3><p>How far a protocol has moved from bounded design into repeated operational feedback.</p><p class="vocabulary-line">{vocabulary_html(maturity_vocabulary)}</p><p class="evidence-counts">{counts_html(maturity_counts, maturity_vocabulary)}</p></div>
        <div class="evidence-axis"><h3>Evidence</h3><p>What kind of source inspection, run report, reproduction, or field operation supports a use case.</p><p class="vocabulary-line">{vocabulary_html(evidence_vocabulary)}</p><p class="evidence-counts">{counts_html(evidence_counts, evidence_vocabulary)}</p></div>
        <div class="evidence-axis"><h3>Conformance</h3><p>How directly the named requirements were mapped, inspected, or executed, with declared gaps preserved.</p><p class="vocabulary-line">{vocabulary_html(conformance_vocabulary)}</p><p class="evidence-counts">{counts_html(conformance_counts, conformance_vocabulary)}</p></div>
      </div>
      <p class="evidence-counts"><span><code>{len(usecases)}</code> manifest-listed use cases · <code>{verified_count}</code> verified conformance claims. Read each evidence scope before reusing a conclusion.</span></p>
    </div>
  </section>

  <section id="authority" class="landing-section">
    <div class="shell authority-grid">
      <div><span class="section-number">04 · Authority</span><h2>The website never becomes a second specification.</h2></div>
      <div class="authority-source">
        <ul>
          <li><strong>protocols.yaml</strong> is canonical for routing, ids, versions, maturity labels, and shared vocabularies.</li>
          <li><strong>Protocol documents</strong> define their own semantics, invariants, schemas, and conformance rules.</li>
          <li><strong>Use cases</strong> provide evidence and binding guidance; they do not redefine a protocol.</li>
          <li>A conflict between the manifest and a document is a repository defect—surface it instead of guessing.</li>
        </ul>
        <div class="section-actions"><a class="button button-primary" href="{BASE_URL}protocols.yaml">Open machine-readable authority <span class="arrow" aria-hidden="true">→</span></a></div>
      </div>
    </div>
  </section>

  <section id="adopt" class="landing-section">
    <div class="shell adopt-grid">
      <div>
        <span class="section-number">05 · Adopt</span><h2>One protocol. One bounded attempt.</h2>
        <p class="section-intro">Partial and negative results are useful. Record the route, runtime, observed result, remaining gaps, and friction without upgrading the claim.</p>
        <div class="section-actions">
          <a class="button button-primary" href="{BASE_URL}docs/agent-adoption-guide.html">Read the Adoption Guide <span class="arrow" aria-hidden="true">→</span></a>
          <a class="button external-link" href="{REPO_URL}/issues/new?template=adoption-experience.yml">Report an adoption experience</a>
        </div>
      </div>
      <ol class="adopt-steps">{steps_html}</ol>
    </div>
  </section>
</div>""".strip()

    structured = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "agent-wiki",
        "description": SITE_DESCRIPTION,
        "url": BASE_URL,
        "license": LICENSE_URL,
        "codeRepository": REPO_URL,
        "hasPart": [
            {
                "@type": "TechArticle",
                "name": str(protocol["name"]),
                "url": html_url_for_markdown(PurePosixPath(str(protocol["document"]))),
                "version": str(protocol["version"]),
            }
            for protocol in protocols
        ],
    }
    values = page_values(
        title="agent-wiki — LLM agent memory and coordination protocols",
        description=SITE_DESCRIPTION,
        canonical=BASE_URL,
        markdown_alternate=BASE_URL + "index.md",
        main=main,
        main_class="landing-main",
        body_class="landing-page",
        structured_data=structured,
        revision=revision,
    )
    return render_template(template, values)


def generate_index_markdown(
    manifest: Mapping[str, Any], routes: Sequence[AdoptionRoute]
) -> str:
    protocols, guides, usecases = manifest_collections(manifest)
    conformance_counts = Counter(str(item["conformance"]) for item in usecases)
    lines = [
        "# agent-wiki",
        "",
        SITE_DESCRIPTION,
        "",
        "This is a generated machine-readable index. The source repository and `protocols.yaml` remain authoritative.",
        "",
        "## Start here",
        "",
        f"- [Protocol manifest]({BASE_URL}protocols.yaml) — Canonical ids, versions, maturity, vocabularies, dependencies, artifacts, and usecase evidence.",
        f"- [Agent Adoption Guide]({BASE_URL}docs/agent-adoption-guide.md) — Select one protocol and its smallest sufficient binding.",
        f"- [Repository README]({BASE_URL}README.md) — Positioning, source authority, and contribution boundaries.",
        "",
        "## Protocol registry",
        "",
        "| Protocol | Version | Maturity | Minimum | Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for protocol in protocols:
        document = PurePosixPath(str(protocol["document"]))
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_escape_cell(protocol["name"]),
                    f"`{markdown_escape_cell(protocol['version'])}`",
                    f"`{markdown_escape_cell(protocol['maturity'])}`",
                    f"`{markdown_escape_cell(protocol['minimal_level'])}`",
                    f"[Markdown]({source_url(document)})",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Select by current problem",
            "",
            "| Current problem | Start with | Minimum | First artifact or action |",
            "| --- | --- | --- | --- |",
        ]
    )
    for route in routes:
        target, fragment = resolved_repo_path(
            PurePosixPath("docs/agent-adoption-guide.md"), route.href
        )
        target_url = source_url(target)
        if fragment:
            target_url += "#" + quote(fragment, safe="-._~")
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_escape_cell(route.problem),
                    f"[{markdown_escape_cell(route.label)}]({target_url})",
                    f"`{markdown_escape_cell(route.minimum)}`",
                    markdown_escape_cell(route.first_action),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Evidence snapshot",
            "",
            f"- Protocols: {len(protocols)}",
            f"- Guides: {len(guides)}",
            f"- Manifest-listed use cases: {len(usecases)}",
            f"- Verified conformance claims: {conformance_counts.get('verified', 0)}",
            "",
            "Maturity, evidence, and conformance are separate axes. Read the declared scope before reusing a claim.",
            "",
            "## Contribute an observation",
            "",
            f"- [Report an adoption experience]({REPO_URL}/issues/new?template=adoption-experience.yml)",
            f"- [Repository]({REPO_URL})",
            "",
        ]
    )
    return "\n".join(lines)


def generate_llms_txt(
    manifest: Mapping[str, Any], source_markdown: Sequence[PurePosixPath]
) -> tuple[str, set[str]]:
    protocols, guides, usecases = manifest_collections(manifest)
    lines = [
        "# agent-wiki",
        "",
        f"> {SITE_DESCRIPTION}",
        "",
        "Use protocols.yaml for routing and closed vocabularies. Read one selected protocol completely before claiming conformance. Maturity, evidence, and conformance are separate axes.",
        "",
        "## Start here",
        "",
        f"- [Machine index]({BASE_URL}index.md): Compact generated routing and evidence snapshot.",
        f"- [Protocol manifest]({BASE_URL}protocols.yaml): Canonical protocol ids, versions, maturity, vocabularies, dependencies, artifacts, and usecase evidence.",
        f"- [Agent Adoption Guide]({BASE_URL}docs/agent-adoption-guide.md): Smallest reading and binding path for a new Agent.",
        "",
        "## Protocols",
        "",
    ]
    linked: set[str] = {"index.md", "protocols.yaml", "docs/agent-adoption-guide.md"}
    for protocol in protocols:
        document = PurePosixPath(str(protocol["document"]))
        linked.add(document.as_posix())
        lines.append(
            f"- [{protocol['name']}]({source_url(document)}): "
            f"{protocol['id']}@{protocol['version']}; {protocol['maturity']}; "
            f"minimum {protocol['minimal_level']}."
        )
    lines.extend(["", "## Guides", ""])
    for guide in guides:
        document = PurePosixPath(str(guide["document"]))
        linked.add(document.as_posix())
        lines.append(
            f"- [{guide['id']}]({source_url(document)}): "
            f"{guide['maturity']}; {guide['read_when']}"
        )
    lines.extend(["", "## Use cases", ""])
    for case in usecases:
        document = PurePosixPath(str(case["document"]))
        linked.add(document.as_posix())
        lines.append(
            f"- [{case['id']}]({source_url(document)}): "
            f"evidence {case['evidence']}; conformance {case['conformance']}; "
            f"protocol {case['protocol_id']}."
        )
    remaining = [path for path in source_markdown if path.as_posix() not in linked]
    if remaining:
        lines.extend(["", "## Additional source indexes", ""])
        for document in remaining:
            linked.add(document.as_posix())
            label = "Repository README" if document == PurePosixPath("README.md") else document.as_posix()
            lines.append(f"- [{label}]({source_url(document)}): Additional source navigation or repository context.")
    lines.extend(
        [
            "",
            "## Optional",
            "",
            f"- [Human reading surface]({BASE_URL}): Generated HTML navigation; not a second source of protocol semantics.",
            f"- [GitHub repository]({REPO_URL}): Source, history, issues, and contribution workflow.",
            f"- [Adoption experience report]({REPO_URL}/issues/new?template=adoption-experience.yml): Share partial, negative, or successful bounded attempts without implying conformance.",
            "",
        ]
    )
    return "\n".join(lines), linked


def generate_sitemap(html_paths: Iterable[PurePosixPath]) -> str:
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ElementTree.register_namespace("", namespace)
    root = ElementTree.Element(f"{{{namespace}}}urlset")
    urls = [BASE_URL]
    urls.extend(
        BASE_URL + quote(path.as_posix(), safe="/-._~")
        for path in sorted(set(html_paths), key=lambda item: item.as_posix())
        if path.as_posix() not in {"index.html", "404.html"}
    )
    for url in urls:
        item = ElementTree.SubElement(root, f"{{{namespace}}}url")
        ElementTree.SubElement(item, f"{{{namespace}}}loc").text = url
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ElementTree.tostring(
        root, encoding="unicode", short_empty_elements=True
    ) + "\n"


def generate_robots_txt() -> str:
    return f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n"


def render_404(template: str, revision: str) -> str:
    main = f"""
<div class="not-found-inner">
  <h1>Page not found.</h1>
  <p>The public surface may have changed with the protocol source. Return to the generated index or route from the canonical manifest.</p>
  <div class="hero-actions">
    <a class="button button-primary" href="{BASE_URL}">Return home <span class="arrow" aria-hidden="true">→</span></a>
    <a class="button" href="{BASE_URL}protocols.yaml">Open the manifest</a>
  </div>
</div>""".strip()
    structured = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "Page not found",
        "url": BASE_URL + "404.html",
        "isPartOf": {"@type": "WebSite", "name": "agent-wiki", "url": BASE_URL},
    }
    values = page_values(
        title="Page not found · agent-wiki",
        description="The requested agent-wiki page does not exist.",
        canonical=BASE_URL + "404.html",
        markdown_alternate=BASE_URL + "404.md",
        main=main,
        main_class="not-found",
        body_class="not-found-page",
        structured_data=structured,
        revision=revision,
        asset_prefix=BASE_URL,
        robots='<meta name="robots" content="noindex,follow">',
        include_footer=False,
    )
    return render_template(template, values)


def git_revision() -> str:
    candidate = os.environ.get("GITHUB_SHA", "").strip()
    if re.fullmatch(r"[0-9a-fA-F]{40}", candidate):
        return candidate.lower()
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise BuildError("cannot determine the source git revision") from exc
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        fail(f"git returned an invalid revision: {revision!r}")
    return revision


def inspect_html(path: Path) -> HtmlInspection:
    parser = PageInspector()
    try:
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
    except (OSError, UnicodeError) as exc:
        raise BuildError(f"cannot inspect HTML {path.relative_to(OUT)}: {exc}") from exc
    return parser.result()


def expected_canonical(relative: PurePosixPath) -> str:
    return BASE_URL if relative.as_posix() == "index.html" else BASE_URL + quote(
        relative.as_posix(), safe="/-._~"
    )


def expected_markdown_alternate(relative: PurePosixPath) -> str:
    if relative.as_posix() == "index.html":
        return BASE_URL + "index.md"
    return BASE_URL + quote(relative.with_suffix(".md").as_posix(), safe="/-._~")


def resolve_internal_output_link(
    page: PurePosixPath, href: str
) -> tuple[PurePosixPath, str] | None:
    parsed = urlsplit(href)
    if parsed.scheme in {"mailto", "tel", "data", "javascript"}:
        return None
    base = urlsplit(BASE_URL)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme not in {"http", "https"} or parsed.netloc != base.netloc:
            return None
        if not parsed.path.startswith(base.path):
            return None
        path = unquote(parsed.path[len(base.path) :])
    elif parsed.path.startswith("/"):
        if not parsed.path.startswith(base.path):
            return None
        path = unquote(parsed.path[len(base.path) :])
    else:
        path = unquote(parsed.path)
        path = posixpath.normpath(posixpath.join(page.parent.as_posix(), path)) if path else page.as_posix()
    if path in {"", "."} or path.endswith("/"):
        path = path.rstrip("/")
        path = f"{path}/index.html" if path else "index.html"
    path = posixpath.normpath(path)
    if path == ".." or path.startswith("../") or path.startswith("/"):
        fail(f"internal link escapes _site: {page} -> {href}")
    return PurePosixPath(path), unquote(parsed.fragment)


def verify_click_reachability(
    inspections: Mapping[PurePosixPath, HtmlInspection],
    html_paths: Sequence[PurePosixPath],
) -> None:
    """Require every published content page to be reachable via HTML anchors."""
    excluded = {PurePosixPath("404.html")}
    expected = set(html_paths) - excluded
    start = PurePosixPath("index.html")
    if start not in expected:
        fail("click-reachability graph has no index.html entry point")

    reachable: set[PurePosixPath] = set()
    pending = [start]
    while pending:
        page = pending.pop()
        if page in reachable:
            continue
        reachable.add(page)
        for href in inspections[page].anchor_hrefs:
            resolved = resolve_internal_output_link(page, href)
            if resolved is None:
                continue
            target, _ = resolved
            if target in expected and target not in reachable:
                pending.append(target)

    if reachable != expected:
        missing = ", ".join(path.as_posix() for path in sorted(expected - reachable))
        fail(f"HTML pages are not reachable from index.html anchors: {missing}")


def verify_html_pages(html_paths: Sequence[PurePosixPath]) -> None:
    inspections: dict[PurePosixPath, HtmlInspection] = {}
    for relative in html_paths:
        path = output_path(relative)
        inspection = inspect_html(path)
        inspections[relative] = inspection
        if inspection.h1_count != 1:
            fail(f"{relative} has {inspection.h1_count} H1 elements; expected exactly 1")
        if inspection.duplicate_ids:
            fail(
                f"{relative} has duplicate ids: {', '.join(sorted(inspection.duplicate_ids))}"
            )
        canonical = expected_canonical(relative)
        if inspection.canonicals != [canonical]:
            fail(f"{relative} canonical is {inspection.canonicals!r}; expected [{canonical!r}]")
        if inspection.describedby != [BASE_URL + "llms.txt"]:
            fail(f"{relative} must have exactly one llms.txt describedby link")
        alternate = expected_markdown_alternate(relative)
        if inspection.markdown_alternates != [alternate]:
            fail(
                f"{relative} Markdown alternate is {inspection.markdown_alternates!r}; "
                f"expected [{alternate!r}]"
            )
        description_sets = (
            inspection.descriptions,
            inspection.open_graph_descriptions,
            inspection.twitter_descriptions,
        )
        if any(len(values) != 1 for values in description_sets):
            fail(f"{relative} must have exactly one HTML, Open Graph, and Twitter description")
        descriptions = [values[0] for values in description_sets]
        if len(set(descriptions)) != 1:
            fail(f"{relative} publishes inconsistent description metadata")
        if (
            relative != PurePosixPath("404.html")
            and inspection.structured_descriptions != [descriptions[0]]
        ):
            fail(f"{relative} JSON-LD description does not match its visible metadata")
        if not 40 <= len(descriptions[0]) <= 157:
            fail(
                f"{relative} description length is {len(descriptions[0])}; expected 40..157"
            )
        if "…" in descriptions[0]:
            fail(f"{relative} description must preserve complete source-derived prose")
        if relative == PurePosixPath("404.html"):
            required_assets = {
                BASE_URL + "assets/favicon.svg",
                BASE_URL + "assets/site.css",
            }
            if not required_assets.issubset(inspection.hrefs):
                fail("404.html assets must remain absolute for deep-path fallbacks")

    for page, inspection in inspections.items():
        for href in inspection.hrefs:
            resolved = resolve_internal_output_link(page, href)
            if resolved is None:
                continue
            target, fragment = resolved
            target_path = output_path(target)
            if not target_path.is_file():
                fail(f"broken internal link: {page} -> {href} (missing {target})")
            if fragment:
                if target.suffix.lower() != ".html":
                    # Raw Markdown/YAML is deliberately copied for agents; HTTP
                    # fragments on those source representations are opaque.
                    continue
                target_inspection = inspections.get(target)
                if target_inspection is None:
                    target_inspection = inspect_html(target_path)
                    inspections[target] = target_inspection
                if fragment not in target_inspection.ids:
                    fail(
                        f"broken internal anchor: {page} -> {href} "
                        f"(#{fragment} absent in {target})"
                    )

    verify_click_reachability(inspections, html_paths)


def verify_seo_surfaces(
    manifest: Mapping[str, Any],
    routes: Sequence[AdoptionRoute],
    metadata: Mapping[PurePosixPath, DocumentMeta],
    adoption_source: str,
    parser: MarkdownIt,
) -> None:
    protocols, guides, usecases = manifest_collections(manifest)
    protocols_by_id = {str(protocol["id"]): protocol for protocol in protocols}
    route_groups = routes_by_document(routes)
    minimal_anchors = extract_minimal_binding_anchors(adoption_source, parser)
    total_glances = 0
    total_glance_usecases = 0
    total_backlinks = 0
    verified_usecase_indexes: dict[PurePosixPath, str] = {}

    for protocol in protocols:
        document = PurePosixPath(str(protocol["document"]))
        inspection = inspect_html(output_path(document.with_suffix(".html")))
        expected_description = metadata[document].description
        if inspection.descriptions != [expected_description]:
            fail(f"protocol {protocol['id']} description drifted from its derived source")
        document_routes = route_groups.get(document, [])
        if not document_routes:
            fail(f"protocol {protocol['id']} has no route for SEO verification")
        cases = [
            as_mapping(item, f"protocol {protocol['id']}.usecases")
            for item in as_list(protocol["usecases"], f"protocol {protocol['id']}.usecases")
        ]
        expected_glance = [
            (
                str(protocol["id"]),
                str(protocol["maturity"]),
                str(len(cases)),
                str(len(document_routes)),
            )
        ]
        if inspection.glance_protocols != expected_glance:
            fail(f"protocol {protocol['id']} At a glance metadata does not match its sources")
        if inspection.glance_problem_texts != [route.problem for route in document_routes]:
            fail(f"protocol {protocol['id']} visible problems do not match the Adoption Guide")
        if inspection.glance_minimum_texts != [str(protocol["minimal_level"])]:
            fail(f"protocol {protocol['id']} visible minimum does not match the manifest")
        route_labels = {route.label for route in document_routes}
        expected_start_hrefs = (
            [minimal_anchors[next(iter(route_labels))]] if len(route_labels) == 1 else []
        )
        if inspection.glance_start_hrefs != expected_start_hrefs:
            fail(f"protocol {protocol['id']} Start at link does not match section 4")
        if inspection.glance_maturity_texts != [str(protocol["maturity"])]:
            fail(f"protocol {protocol['id']} visible maturity does not match the manifest")
        expected_usecases = [
            (
                str(case["id"]),
                str(case["evidence"]),
                str(case["conformance"]),
                html_url_for_markdown(PurePosixPath(str(case["document"]))),
            )
            for case in cases
        ]
        if inspection.glance_usecases != expected_usecases:
            fail(f"protocol {protocol['id']} At a glance usecases do not match the manifest")
        if inspection.glance_usecase_labels != [str(case["id"]) for case in cases]:
            fail(f"protocol {protocol['id']} visible usecase labels do not match the manifest")
        if inspection.glance_evidence_texts != [str(case["evidence"]) for case in cases]:
            fail(f"protocol {protocol['id']} visible evidence tokens do not match the manifest")
        if inspection.glance_conformance_texts != [
            str(case["conformance"]) for case in cases
        ]:
            fail(
                f"protocol {protocol['id']} visible conformance tokens do not match the manifest"
            )
        if inspection.protocol_backlinks:
            fail(f"protocol {protocol['id']} unexpectedly contains a parent-protocol backlink")
        if cases:
            index_parents = {
                PurePosixPath(str(case["document"])).parent
                for case in cases
            }
            if len(index_parents) != 1:
                fail(f"protocol {protocol['id']} use cases span multiple index directories")
            index_document = next(iter(index_parents)) / "README.md"
            owner = verified_usecase_indexes.get(index_document)
            if owner is not None:
                fail(
                    f"use-case index {index_document} is shared by protocols "
                    f"{owner} and {protocol['id']}"
                )
            verified_usecase_indexes[index_document] = str(protocol["id"])
            index_inspection = inspect_html(
                output_path(index_document.with_suffix(".html"))
            )
            if index_inspection.descriptions != [metadata[index_document].description]:
                fail(
                    f"protocol {protocol['id']} use-case index description "
                    "drifted from the manifest"
                )
        total_glances += len(inspection.glance_protocols)
        total_glance_usecases += len(inspection.glance_usecases)

    expected_index_count = sum(
        bool(as_list(protocol["usecases"], f"protocol {protocol['id']}.usecases"))
        for protocol in protocols
    )
    if len(verified_usecase_indexes) != expected_index_count:
        fail(
            f"verified {len(verified_usecase_indexes)} use-case indexes; "
            f"expected {expected_index_count}"
        )

    for guide in guides:
        document = PurePosixPath(str(guide["document"]))
        inspection = inspect_html(output_path(document.with_suffix(".html")))
        if inspection.descriptions != [metadata[document].description]:
            fail(f"guide {guide['id']} description drifted from its derived source")
        if (
            inspection.glance_protocols
            or inspection.glance_problem_texts
            or inspection.glance_usecases
            or inspection.protocol_backlinks
        ):
            fail(f"guide {guide['id']} unexpectedly contains protocol relationship UI")

    for case in usecases:
        document = PurePosixPath(str(case["document"]))
        inspection = inspect_html(output_path(document.with_suffix(".html")))
        if inspection.descriptions != [metadata[document].description]:
            fail(f"usecase {case['id']} description drifted from its derived source")
        parent = protocols_by_id[str(case["protocol_id"])]
        expected_backlink = [
            (
                str(parent["id"]),
                html_url_for_markdown(PurePosixPath(str(parent["document"]))),
            )
        ]
        if inspection.protocol_backlinks != expected_backlink:
            fail(f"usecase {case['id']} parent-protocol backlink does not match the manifest")
        if (
            inspection.glance_protocols
            or inspection.glance_problem_texts
            or inspection.glance_usecases
        ):
            fail(f"usecase {case['id']} unexpectedly contains a protocol At a glance block")
        total_backlinks += len(inspection.protocol_backlinks)

    if total_glances != len(protocols):
        fail(f"expected {len(protocols)} protocol At a glance blocks, found {total_glances}")
    if total_glance_usecases != len(usecases):
        fail(
            f"expected {len(usecases)} manifest usecases in At a glance blocks, "
            f"found {total_glance_usecases}"
        )
    if total_backlinks != len(usecases):
        fail(f"expected {len(usecases)} usecase protocol backlinks, found {total_backlinks}")


def verify_source_identity(source_bytes: Mapping[PurePosixPath, bytes]) -> None:
    for relative, expected in source_bytes.items():
        destination = output_path(relative)
        if not destination.is_file():
            fail(f"source representation was not copied: {relative}")
        actual = destination.read_bytes()
        if actual != expected:
            fail(f"source representation is not byte-identical: {relative}")


def verify_sitemap(html_paths: Sequence[PurePosixPath]) -> None:
    sitemap_path = output_path("sitemap.xml")
    try:
        tree = ElementTree.parse(sitemap_path)
    except (OSError, ElementTree.ParseError) as exc:
        raise BuildError(f"invalid sitemap.xml: {exc}") from exc
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    entries = tree.findall("s:url", namespace)
    locations = [entry.findtext("s:loc", default="", namespaces=namespace) for entry in entries]
    expected_locations = [BASE_URL]
    expected_locations.extend(
        BASE_URL + quote(path.as_posix(), safe="/-._~")
        for path in sorted(set(html_paths), key=lambda item: item.as_posix())
        if path.as_posix() not in {"index.html", "404.html"}
    )
    if locations != expected_locations:
        fail("sitemap.xml URL set or order does not match the generated HTML set")
    if tree.findall("s:url/s:lastmod", namespace):
        fail("sitemap.xml must not publish a lastmod without per-page modification data")


def verify_robots_txt() -> None:
    robots_path = output_path("robots.txt")
    try:
        actual = robots_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise BuildError(f"cannot read robots.txt: {exc}") from exc
    expected = generate_robots_txt()
    if actual != expected:
        fail("robots.txt does not match the generated crawl policy")


def verify_llms(
    linked: set[str], source_markdown: Sequence[PurePosixPath], manifest: Mapping[str, Any]
) -> None:
    expected = {path.as_posix() for path in source_markdown}
    expected.update({"index.md", "protocols.yaml"})
    if linked != expected:
        missing = sorted(expected - linked)
        extra = sorted(linked - expected)
        fail(f"llms.txt coverage mismatch; missing={missing}, extra={extra}")
    text = output_path("llms.txt").read_text(encoding="utf-8")
    for relative in sorted(expected):
        url = BASE_URL + quote(relative, safe="/-._~")
        if url not in text:
            fail(f"llms.txt does not link {relative}")
    protocols, guides, usecases = manifest_collections(manifest)
    for expected_heading in ("# agent-wiki", "## Start here", "## Protocols", "## Guides", "## Use cases"):
        if expected_heading not in text:
            fail(f"llms.txt is missing required heading {expected_heading!r}")
    if len(protocols) == 0 or len(guides) == 0 or len(usecases) == 0:
        fail("manifest collection counts unexpectedly dropped to zero")


def verify_counts(
    manifest: Mapping[str, Any], routes: Sequence[AdoptionRoute]
) -> None:
    protocols, guides, usecases = manifest_collections(manifest)
    verified = sum(1 for item in usecases if item["conformance"] == "verified")
    landing = output_path("index.html").read_text(encoding="utf-8")
    expected_attributes = {
        "data-protocol-count": len(protocols),
        "data-guide-count": len(guides),
        "data-usecase-count": len(usecases),
        "data-problem-count": len(routes),
        "data-verified-count": verified,
    }
    for attribute, count in expected_attributes.items():
        if f'{attribute}="{count}"' not in landing:
            fail(f"landing page {attribute} does not match the source count {count}")
    index_markdown = output_path("index.md").read_text(encoding="utf-8")
    for label, count in (
        ("Protocols", len(protocols)),
        ("Guides", len(guides)),
        ("Manifest-listed use cases", len(usecases)),
        ("Verified conformance claims", verified),
    ):
        if f"- {label}: {count}" not in index_markdown:
            fail(f"index.md count for {label} does not match {count}")


def verify_no_symlinks() -> None:
    for path in OUT.rglob("*"):
        relative = PurePosixPath(path.relative_to(OUT).as_posix())
        if path.is_symlink():
            fail(f"publication artifact contains a symlink: {relative}")
        if relative != PurePosixPath(".nojekyll") and any(
            part.startswith(".") for part in relative.parts
        ):
            fail(f"publication artifact contains a hidden path: {relative}")


def build() -> None:
    manifest = load_manifest()
    parser = make_markdown_parser()
    verify_text_extractors(parser)
    source_markdown = discover_source_markdown()
    source_paths = [*source_markdown, PurePosixPath("protocols.yaml"), PurePosixPath("LICENSE")]
    source_bytes: dict[PurePosixPath, bytes] = {}
    for relative in source_paths:
        source = ROOT.joinpath(*relative.parts)
        if not source.is_file():
            fail(f"required source file does not exist: {relative}")
        source_bytes[relative] = source.read_bytes()

    try:
        source_texts = {
            relative: source_bytes[relative].decode("utf-8") for relative in source_markdown
        }
        adoption_source = source_texts[PurePosixPath("docs/agent-adoption-guide.md")]
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeError, KeyError) as exc:
        raise BuildError(f"cannot read site inputs: {exc}") from exc
    routes = extract_adoption_routes(adoption_source, parser)
    adoption_steps = extract_adoption_steps(adoption_source, parser)
    metadata = document_metadata(manifest, routes, source_texts, parser)
    revision = git_revision()

    if OUT.is_symlink():
        fail("_site must not be a symlink")
    if OUT.exists():
        if not OUT.is_dir() or OUT.resolve().parent != ROOT.resolve():
            fail("refusing to replace an unsafe _site path")
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    for relative, value in source_bytes.items():
        write_bytes(relative, value)
    for asset_relative in ASSET_FILES:
        asset = ASSET_DIR.joinpath(*asset_relative.parts)
        if asset.is_symlink() or not asset.is_file():
            fail(f"required site asset is absent or unsafe: site/assets/{asset_relative}")
        write_bytes(PurePosixPath("assets") / asset_relative, asset.read_bytes())

    rendered_source_paths = render_source_pages(
        source_markdown=source_markdown,
        source_texts=source_texts,
        parser=parser,
        template=template,
        manifest=manifest,
        metadata=metadata,
        routes=routes,
        revision=revision,
    )
    index_markdown = generate_index_markdown(manifest, routes)
    write_text("index.md", index_markdown)
    write_text("index.html", render_landing(
        manifest=manifest,
        routes=routes,
        adoption_steps=adoption_steps,
        template=template,
        revision=revision,
    ))
    llms_text, llms_linked = generate_llms_txt(manifest, source_markdown)
    write_text("llms.txt", llms_text)
    write_text("404.md", "# Page not found\n\nReturn to the [agent-wiki machine index](index.md).\n")
    write_text("404.html", render_404(template, revision))

    html_paths = [PurePosixPath("index.html"), *rendered_source_paths, PurePosixPath("404.html")]
    write_text("sitemap.xml", generate_sitemap(html_paths))
    write_text("robots.txt", generate_robots_txt())
    write_text(".nojekyll", "")

    verify_no_symlinks()
    verify_source_identity(source_bytes)
    verify_html_pages(html_paths)
    verify_seo_surfaces(manifest, routes, metadata, adoption_source, parser)
    verify_sitemap(html_paths)
    verify_robots_txt()
    verify_llms(llms_linked, source_markdown, manifest)
    verify_counts(manifest, routes)

    protocols, guides, usecases = manifest_collections(manifest)
    print(
        "Built and verified _site: "
        f"{len(source_markdown)} source Markdown files, "
        f"{len(html_paths)} HTML pages, {len(protocols)} protocols, "
        f"{len(guides)} guides, {len(usecases)} use cases, "
        f"{len(routes)} problem routes."
    )


def main() -> int:
    try:
        build()
    except BuildError as exc:
        print(f"build_pages.py: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
