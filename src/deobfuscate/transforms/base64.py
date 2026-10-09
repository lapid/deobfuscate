import base64
import binascii
import re
from collections.abc import Iterable

from deobfuscate.transforms.base import Candidate, Transform, is_readable

# A run of base64 characters that is not part of a longer word-like run.
TOKEN = re.compile(r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/_-]{16,}={0,2}(?![A-Za-z0-9+/=_-])")
URL_SAFE = str.maketrans("-_", "+/")


class Base64(Transform):
    name = "base64"

    def propose(self, text: str) -> Iterable[Candidate]:
        for match in TOKEN.finditer(text):
            token = match.group()
            # Both alphabets in one token is not base64.
            if ("-" in token or "_" in token) and ("+" in token or "/" in token):
                continue
            body = token.rstrip("=").translate(URL_SAFE)
            if len(body) % 4 == 1:
                continue
            try:
                decoded = base64.b64decode(body + "=" * (-len(body) % 4), validate=True).decode("utf-8")
            except (binascii.Error, UnicodeDecodeError):
                continue
            if decoded and is_readable(decoded):
                yield Candidate(match.start(), match.end(), decoded)
