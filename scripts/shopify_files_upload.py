"""Upload local image files to Shopify Files via Admin GraphQL.

Steps per file:
  1) stagedUploadsCreate -> get presigned upload target
  2) POST file as multipart/form-data to that target
  3) fileCreate(originalSource=resourceUrl) -> register file in Shopify
  4) poll Files.url until READY -> public CDN URL

Usage:
  python scripts/shopify_files_upload.py path1.png path2.png ...

Reads SHOPIFY_STORE / SHOPIFY_TOKEN from ../.env. Requires write_files scope on token.
"""

import json
import mimetypes
import sys
import time
import uuid
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
API_VERSION = "2024-01"


def load_env() -> dict:
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def gql(store: str, token: str, query: str, variables: dict) -> dict:
    url = f"https://{store}/admin/api/{API_VERSION}/graphql.json"
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("X-Shopify-Access-Token", token)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GraphQL HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}") from e
    if data.get("errors"):
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data["data"]


STAGED_UPLOADS_CREATE = """
mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
  stagedUploadsCreate(input: $input) {
    stagedTargets {
      url
      resourceUrl
      parameters { name value }
    }
    userErrors { field message }
  }
}
"""

FILE_CREATE = """
mutation fileCreate($files: [FileCreateInput!]!) {
  fileCreate(files: $files) {
    files {
      id
      fileStatus
      ... on MediaImage {
        image { url width height }
      }
    }
    userErrors { field message }
  }
}
"""

FILE_BY_ID = """
query fileNode($id: ID!) {
  node(id: $id) {
    ... on MediaImage {
      id
      fileStatus
      image { url width height }
    }
  }
}
"""


def staged_upload(store: str, token: str, path: Path) -> str:
    size = path.stat().st_size
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    res = gql(store, token, STAGED_UPLOADS_CREATE, {
        "input": [{
            "resource": "FILE",
            "filename": path.name,
            "mimeType": mime,
            "httpMethod": "POST",
            "fileSize": str(size),
        }],
    })
    sc = res["stagedUploadsCreate"]
    if sc["userErrors"]:
        raise RuntimeError(f"stagedUploadsCreate userErrors: {sc['userErrors']}")
    target = sc["stagedTargets"][0]
    upload_url = target["url"]
    params = {p["name"]: p["value"] for p in target["parameters"]}
    resource_url = target["resourceUrl"]

    boundary = f"----boundary{uuid.uuid4().hex}"
    body = bytearray()
    for k, v in params.items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode("utf-8")
    body += (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
        f"Content-Type: {mime}\r\n\r\n"
    ).encode("utf-8")
    body += path.read_bytes()
    body += f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(upload_url, data=bytes(body), method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"staged upload HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}") from e
    return resource_url


def register_file(store: str, token: str, resource_url: str, alt: str) -> str:
    res = gql(store, token, FILE_CREATE, {
        "files": [{
            "originalSource": resource_url,
            "alt": alt,
            "contentType": "IMAGE",
        }],
    })
    fc = res["fileCreate"]
    if fc["userErrors"]:
        raise RuntimeError(f"fileCreate userErrors: {fc['userErrors']}")
    return fc["files"][0]["id"]


def poll_file_url(store: str, token: str, file_id: str, max_wait: int = 60) -> str:
    start = time.time()
    while True:
        res = gql(store, token, FILE_BY_ID, {"id": file_id})
        node = res.get("node") or {}
        status = node.get("fileStatus")
        url = (node.get("image") or {}).get("url")
        if status == "READY" and url:
            return url
        if status == "FAILED":
            raise RuntimeError(f"file {file_id} status FAILED: {node}")
        if time.time() - start > max_wait:
            raise TimeoutError(f"file {file_id} still {status} after {max_wait}s")
        time.sleep(2)


def upload_one(store: str, token: str, path: Path, alt: str) -> str:
    print(f"[{path.name}] staging...", flush=True)
    resource_url = staged_upload(store, token, path)
    print(f"[{path.name}] registering...", flush=True)
    file_id = register_file(store, token, resource_url, alt)
    print(f"[{path.name}] polling for CDN URL...", flush=True)
    url = poll_file_url(store, token, file_id)
    print(f"[{path.name}] -> {url}", flush=True)
    return url


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: shopify_files_upload.py <file1> [file2 ...]", file=sys.stderr)
        return 2
    env = load_env()
    store = env.get("SHOPIFY_STORE", "")
    token = env.get("SHOPIFY_TOKEN", "")
    if not store or not token:
        print("missing SHOPIFY_STORE / SHOPIFY_TOKEN in .env", file=sys.stderr)
        return 2

    mapping: dict[str, str] = {}
    for arg in argv[1:]:
        path = Path(arg).resolve()
        if not path.exists():
            print(f"missing: {path}", file=sys.stderr)
            return 1
        url = upload_one(store, token, path, alt=path.stem)
        mapping[str(path)] = url

    print("\n=== mapping ===")
    print(json.dumps(mapping, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
