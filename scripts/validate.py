#!/usr/bin/env python3
"""Small, dependency-free content and HTML validator for this repository."""
from html.parser import HTMLParser
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("README.md", "FAQ.md", "SECURITY.md", "index.html", "metadata.json")
FORBIDDEN = ("https://sherlockbot.is", "https://glazboga.is", "https://t.me/", "https://telegram.me/")


class HTMLCheck(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = []
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1":
            self.stack.append(tag)
        if tag == "a" and "href" not in attrs:
            self.errors.append("HTML: ссылка без href")

    def handle_endtag(self, tag):
        if tag == "h1" and self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if self.stack and self.stack[-1] == "h1":
            self.h1.append(data)


def fail(message):
    print(f"ERROR: {message}")


def main():
    errors = []
    for name in REQUIRED:
        if not (ROOT / name).is_file():
            errors.append(f"отсутствует обязательный файл: {name}")
    if errors:
        for error in errors:
            fail(error)
        return 1

    metadata = json.loads((ROOT / "metadata.json").read_text(encoding="utf-8"))
    keyword = metadata.get("keyword", "").strip()
    target = metadata.get("target_url", "").strip()
    if not keyword:
        errors.append("metadata.json: пустой keyword")
    if not target:
        errors.append("metadata.json: пустой target_url")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    faq = (ROOT / "FAQ.md").read_text(encoding="utf-8")
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    if keyword and keyword not in readme.splitlines()[0]:
        errors.append("README: H1 не содержит точный keyword")
    if readme.count(target) < 2:
        errors.append("README: target_url должен быть в начале и в итоговом блоке")
    html_normalized = html.replace("&amp;", "&")
    if target not in html_normalized:
        errors.append("index.html: отсутствует target_url")
    if "Открыть в Telegram" not in html:
        errors.append("index.html: отсутствует CTA-текст")
    if readme.count("![Content validation]") != 1:
        errors.append("README: допустим только один badge workflow")
    combined = "\n".join((readme, faq, security, html_normalized)).lower()
    for domain in FORBIDDEN:
        if domain in combined:
            errors.append(f"запрещённый прямой CTA или домен: {domain}")
    parser = HTMLCheck()
    parser.feed(html)
    if parser.errors:
        errors.extend(parser.errors)
    if not parser.h1:
        errors.append("HTML: отсутствует H1")
    elif keyword and keyword not in "".join(parser.h1):
        errors.append("HTML: H1 не содержит точный keyword")
    if "canonical" in html.lower():
        errors.append("HTML: canonical не должен указывать на CTA")
    if len(faq.split("## ")) - 1 < 4:
        errors.append("FAQ: нужно минимум 4 содержательных вопроса")
    if errors:
        for error in errors:
            fail(error)
        return 1
    print("OK: content validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
