#!/usr/bin/env python3
"""Entry program for news-image-20261126 (Python 3.13, stdlib only).

Validates the finished entry.png beside this file (whole PNG, at most
1024x1024 and 1 MiB), then copies it byte for byte to the output
directory. Two runs write identical bytes; no network is used.
"""
import hashlib
import os
import struct
import sys

MAX_BYTES = 1024 * 1024
MAX_DIM = 1024
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def fail(message):
    print(f"entry check failed: {message}", file=sys.stderr)
    return 1


def validate_png(data):
    if len(data) > MAX_BYTES:
        return f"image is {len(data)} bytes, over the 1 MiB limit"
    if not data.startswith(PNG_SIG):
        return "image does not start with the PNG signature"
    pos = len(PNG_SIG)
    width = height = None
    saw_iend = False
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        end = pos + 12 + length
        if end > len(data):
            return f"chunk {kind!r} runs past the end of the file"
        if kind == b"IHDR":
            width, height = struct.unpack(">II", data[pos + 8:pos + 16])
        if kind == b"IEND":
            saw_iend = True
            break
        pos = end
    if width is None or height is None:
        return "image has no IHDR header"
    if width > MAX_DIM or height > MAX_DIM:
        return f"image is {width}x{height}, over the 1024x1024 limit"
    if not saw_iend:
        return "image has no IEND chunk"
    return None


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    with open(source, "rb") as fh:
        data = fh.read()
    problem = validate_png(data)
    if problem:
        return fail(problem)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.png")
    with open(target, "wb") as fh:
        fh.write(data)
    with open(target, "rb") as fh:
        written = fh.read()
    if written != data:
        return fail("written image differs from the source image")
    digest = hashlib.sha256(written).hexdigest()
    print(f"wrote {target} ({len(written)} bytes, sha256 {digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# Deterministic by construction: the same source bytes are validated
# and copied on every run, so both grader runs produce one image.
