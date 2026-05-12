#!/usr/bin/env python3
"""
List files or batch-rename via Alist API.

Usage:
  list  --path PATH --url URL --user USER --password PASS [--recursive] [--videos-only]
  batch --stdin --url URL --user USER --password PASS
        (reads JSON array of {"path":"...", "name":"..."} from stdin)
"""
import argparse, json, os, sys
import urllib.request

VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".rmvb", ".wmv"}


class AlistClient:
    def __init__(self, url, username, password):
        self.url = url.rstrip("/")
        self.token = self._login(username, password)

    def _req(self, endpoint, data=None):
        url = f"{self.url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = self.token
        body = json.dumps(data, ensure_ascii=False).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())

    def _login(self, username, password):
        res = self._req("/api/auth/login", {"username": username, "password": password})
        return res["data"]["token"] if res and res.get("code") == 200 else None

    def list_files(self, path):
        res = self._req("/api/fs/list", {"path": path, "page": 1, "per_page": 300})
        return res["data"]["content"] if res and res.get("code") == 200 else []

    def rename(self, path, new_name):
        res = self._req("/api/fs/rename", {"path": path, "name": new_name})
        return res and res.get("code") == 200


def walk(client, path, recursive=False):
    items = client.list_files(path) or []
    for item in items:
        full = f"{path.rstrip('/')}/{item['name']}"
        yield item, full
        if recursive and item.get("is_dir"):
            yield from walk(client, full, recursive=True)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)

    p_ls = sub.add_parser("list")
    p_ls.add_argument("--path", required=True)
    p_ls.add_argument("--url", required=True)
    p_ls.add_argument("--user", required=True)
    p_ls.add_argument("--password", required=True)
    p_ls.add_argument("--recursive", action="store_true")
    p_ls.add_argument("--videos-only", action="store_true")

    p_batch = sub.add_parser("batch")
    p_batch.add_argument("--stdin", action="store_true")
    p_batch.add_argument("--url", required=True)
    p_batch.add_argument("--user", required=True)
    p_batch.add_argument("--password", required=True)

    args = parser.parse_args()
    client = AlistClient(args.url, args.user, args.password)
    if not client.token:
        print("Login failed", file=sys.stderr)
        sys.exit(1)

    if args.action == "list":
        for item, full_path in walk(client, args.path, recursive=args.recursive):
            if args.videos_only and not item.get("is_dir"):
                ext = os.path.splitext(item["name"])[1].lower()
                if ext not in VIDEO_EXTS:
                    continue
            size = f"{item.get('size', 0) // 1024 // 1024}MB" if not item.get("is_dir") else "DIR"
            print(f"{full_path}\t{size}")

    elif args.action == "batch":
        ops = json.load(sys.stdin)
        ok, fail, skip = 0, 0, 0
        for op in ops:
            path = op["path"]
            new_name = op["name"]
            old_name = os.path.basename(path)
            if old_name == new_name:
                print(f"SKIP (same): {old_name}")
                skip += 1
                continue
            if client.rename(path, new_name):
                print(f"OK:   {old_name}  →  {new_name}")
                ok += 1
            else:
                print(f"FAIL: {path}")
                fail += 1
        print(f"\nDone: {ok} renamed, {skip} skipped, {fail} failed", file=sys.stderr)


if __name__ == "__main__":
    main()
