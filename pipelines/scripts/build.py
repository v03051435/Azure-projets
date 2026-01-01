#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--registry-server", "--acr-login-server", dest="registry_server", required=True)
    parser.add_argument("--acr-name", default="")
    parser.add_argument("--registry-username", default="")
    parser.add_argument("--registry-password", default="")
    parser.add_argument("--services-file", required=True)
    args = parser.parse_args()

    try:
        with open(args.services_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(
            f"ERROR: services file not found: {args.services_file}",
            file=sys.stderr,
        )
        return 1

    services = data.get("services", {})
    if not services:
        print("No services found to build.")
        return 0

    registry_host = args.registry_server.split("/")[0]
    if args.registry_username and args.registry_password:
        subprocess.run(
            ["docker", "login", registry_host, "-u", args.registry_username, "--password-stdin"],
            input=args.registry_password,
            text=True,
            check=True,
        )
    elif args.acr_name:
        subprocess.run(
            ["az", "acr", "login", "--name", args.acr_name], check=True
        )

    for name, svc in services.items():
        repo = (svc.get("repo") or "").strip()
        build = svc.get("build") or {}
        path = (build.get("path") or "").strip()
        skip = bool(build.get("skip", False))

        if skip:
            print(f"Skipping build for {name} (skip=true)")
            continue
        if not repo or not path:
            print(f"Skipping build for {name} (missing repo/path)")
            continue

        image = f"{args.registry_server}/{repo}:{args.tag}"
        print(f"Building {name} ({repo}) from {path}")
        subprocess.run(["docker", "build", "-t", image, path], check=True)
        subprocess.run(["docker", "push", image], check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
