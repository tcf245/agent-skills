#!/usr/bin/env python3
"""
Manage watch_list entries in alist-organizer config.json.

Usage:
  add    --config CONFIG --path PATH --series-name NAME --type {movie,tv} --year YEAR [--season N] [--update]
  remove --config CONFIG --path PATH
  list   --config CONFIG [--path SUBSTR]
"""
import argparse, json, sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Manage watch_list in alist-organizer config.json")
    sub = parser.add_subparsers(dest="action", required=True)

    p_add = sub.add_parser("add")
    p_add.add_argument("--config", required=True)
    p_add.add_argument("--path", required=True)
    p_add.add_argument("--series-name", required=True)
    p_add.add_argument("--type", required=True, choices=["movie", "tv"])
    p_add.add_argument("--year", required=True, type=int)
    p_add.add_argument("--season", type=int)
    p_add.add_argument("--update", action="store_true", help="Overwrite if path already exists")

    p_rm = sub.add_parser("remove")
    p_rm.add_argument("--config", required=True)
    p_rm.add_argument("--path", required=True)

    p_ls = sub.add_parser("list")
    p_ls.add_argument("--config", required=True)
    p_ls.add_argument("--path", help="Filter by path substring")

    args = parser.parse_args()
    config_path = Path(args.config)

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    watch_list = config.setdefault("watch_list", [])

    if args.action == "list":
        for e in watch_list:
            if args.path and args.path not in e.get("path", ""):
                continue
            print(json.dumps(e, ensure_ascii=False))
        return

    if args.action == "add":
        entry = {
            "path": args.path,
            "series_name": args.series_name,
            "year": args.year,
            "type": args.type,
        }
        if args.type == "tv":
            entry["season"] = args.season if args.season else 1

        idx = next((i for i, e in enumerate(watch_list) if e["path"] == args.path), None)

        if idx is not None:
            if args.update:
                watch_list[idx] = entry
                print(f"Updated: {args.path}", file=sys.stderr)
            else:
                print(f"Already exists (pass --update to overwrite): {args.path}", file=sys.stderr)
                sys.exit(0)
        else:
            watch_list.append(entry)
            print(f"Added: {args.path}", file=sys.stderr)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        print(json.dumps(entry, ensure_ascii=False))
        return

    if args.action == "remove":
        before = len(watch_list)
        config["watch_list"] = [e for e in watch_list if e["path"] != args.path]
        if len(config["watch_list"]) < before:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            print(f"Removed: {args.path}", file=sys.stderr)
        else:
            print(f"Not found: {args.path}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
