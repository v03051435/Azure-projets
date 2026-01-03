#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import time

from utils import get_env_vars, join_cmd, parse_bool

def run_cmd(cmd, dry_run, retries=0, delay_seconds=20):
    print(f"CMD: {join_cmd(cmd)}")
    if dry_run:
        return
    if retries <= 0:
        subprocess.run(cmd, check=True)
        return
    last_err = None
    for attempt in range(1, retries + 1):
        result = subprocess.run(cmd, text=True, capture_output=True)
        if result.returncode == 0:
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(result.stderr.strip())
            return
        msg = (result.stderr or "").lower()
        if "operationinprogress" in msg:
            print(
                f"OperationInProgress, retrying in {delay_seconds}s "
                f"({attempt}/{retries})"
            )
            time.sleep(delay_seconds)
            continue
        last_err = subprocess.CalledProcessError(
            result.returncode,
            cmd,
            output=result.stdout,
            stderr=result.stderr,
        )
        break
    if last_err:
        raise last_err


def print_revision_status(app, rg):
    try:
        state = subprocess.check_output(
            [
                "az",
                "containerapp",
                "show",
                "--name",
                app,
                "--resource-group",
                rg,
                "--query",
                "properties.provisioningState",
                "-o",
                "tsv",
            ],
            text=True,
        ).strip()
        print(f"{app} provisioningState: {state}")
    except subprocess.CalledProcessError:
        print(f"{app} provisioningState: <unavailable>")
    try:
        table = subprocess.check_output(
            [
                "az",
                "containerapp",
                "revision",
                "list",
                "--name",
                app,
                "--resource-group",
                rg,
                "--query",
                "[].{name:name,created:properties.createdTime,health:properties.healthState,active:properties.active}",
                "-o",
                "table",
            ],
            text=True,
        ).strip()
        if table:
            print(f"{app} revisions:\n{table}")
    except subprocess.CalledProcessError:
        print(f"{app} revisions: <unavailable>")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", default="deploy")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--registry-server", "--acr-login-server", dest="registry_server", required=True)
    parser.add_argument("--acr-name", default="")
    parser.add_argument("--registry-username", default="")
    parser.add_argument("--registry-password", default="")
    parser.add_argument("--rg", required=True)
    parser.add_argument("--env", required=True)
    parser.add_argument("--services-file", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(
        f"Action={args.action} tag={args.tag} env={args.env} dryRun={args.dry_run}"
    )

    if args.acr_name:
        run_cmd(["az", "acr", "login", "--name", args.acr_name], args.dry_run)

    try:
        with open(args.services_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(
            f"ERROR: services file not found: {args.services_file}",
            file=sys.stderr,
        )
        sys.exit(1)

    services = data.get("services", {})
    if not services:
        print("No services found.")
        return 0

    deploy_targets = []

    for name, svc in services.items():
        repo = (svc.get("repo") or "").strip()
        if not repo:
            print(f"Skipping {name} (missing repo)")
            continue

        if parse_bool(svc.get("skip", False)):
            print(f"Skipping {name} (service skip=true)")
            continue

        deploy_cfg = (svc.get("deploy") or {}).get(args.env)
        if not deploy_cfg:
            print(f"Skipping {name} (no deploy config for env={args.env})")
            continue

        if parse_bool(deploy_cfg.get("skip", False)):
            print(f"Skipping {name} (env skip=true)")
            continue

        app = (deploy_cfg.get("appName") or "").strip()
        if not app:
            print(
                f"ERROR: {name} missing appName for env={args.env}",
                file=sys.stderr,
            )
            return 1

        deploy_targets.append((name, repo, app, deploy_cfg))

    registry_host = args.registry_server.split("/")[0]

    for name, repo, app, deploy_cfg in deploy_targets:
        image = f"{args.registry_server}/{repo}:{args.tag}"
        env_vars = get_env_vars(deploy_cfg.get("envVars"))
        cmd = [
            "az",
            "containerapp",
            "update",
            "--name",
            app,
            "--resource-group",
            args.rg,
            "--image",
            image,
            "--no-wait",
        ]
        if args.registry_username and args.registry_password:
            run_cmd(
                [
                    "az",
                    "containerapp",
                    "registry",
                    "set",
                    "--name",
                    app,
                    "--resource-group",
                    args.rg,
                    "--server",
                    registry_host,
                    "--username",
                    args.registry_username,
                    "--password",
                    args.registry_password,
                ],
                args.dry_run,
            )
        if env_vars:
            cmd += ["--set-env-vars"] + env_vars
        try:
            run_cmd(cmd, args.dry_run, retries=8, delay_seconds=20)
        except subprocess.CalledProcessError:
            print_revision_status(app, args.rg)
            raise

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
