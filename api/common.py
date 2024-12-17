import hashlib
import os

import httpx


def sha256sum(value: str):
    h = hashlib.sha256()
    input = value.encode("utf-8")
    h.update(input)
    return h.hexdigest()


def format_sha256_as_guid(sha256_hash: str):
    return f"{sha256_hash[:8]}-{sha256_hash[8:12]}-{sha256_hash[12:16]}-{sha256_hash[16:20]}-{sha256_hash[20:32]}"


def generate_guid(fname: str):
    return format_sha256_as_guid(sha256sum(fname))


def get_size(url_or_file: str):
    if url_or_file.startswith("http"):
        return len(httpx.head(url_or_file).content)
    return os.path.getsize(url_or_file)
