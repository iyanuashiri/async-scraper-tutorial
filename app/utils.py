import re
from html.parser import HTMLParser
from typing import Tuple


class _MLStripper(HTMLParser):
    """Minimal HTML stripper used by remove_html_tags below."""

    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, d):
        self.text.append(d)

    def get_data(self):
        return "".join(self.text)


def remove_html_tags(text: str) -> str:
    """Strips HTML tags from a string, including <script>/<style> contents."""
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", text)

    stripper = _MLStripper()
    stripper.feed(text)
    return stripper.get_data()


def fix_url(url: str, company_name: str, wd: str) -> str:
    """Turns a relative Workday job-posting href into an absolute URL."""
    return f"https://{company_name}.{wd}.myworkdayjobs.com{url}"


def break_string(company_url: str) -> Tuple[str, str]:
    """Extracts (company_name, workday_datacenter) from a Workday careers URL."""
    parts = company_url.split(".")
    company_name = parts[0].split("//")[1]
    wd = parts[1]
    return company_name, wd
