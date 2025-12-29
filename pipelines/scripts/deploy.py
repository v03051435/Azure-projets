#!/usr/bin/env python3
import argparse
import json
import shlex
import subprocess
import sys
import time
import urllib.request


def parse_bool(val):
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    return str(val).strip().lower() in ("1", "true", "yes", "y", "on")


def join_cmd(cmd):
    try:
        return shlex.join(cmd)
    except AttributeError:
        return " ".join(shlex.quote(c) for c in cmd)


def get_env_vars(env_vars):
    if not env_vars:
        return []
    if isinstance(env_vars, list):
        return env_vars
    return shlex.split(str(env_vars))


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


def wait_for_update(app, rg, expected_image, timeout_seconds=600, interval=10):
    deadline = time.time() + timeout_seconds
    last_state = ""
    last_image = ""
    while time.time() < deadline:
        try:
            raw = subprocess.check_output(
                [
                    "az",
                    "containerapp",
                    "show",
                    "--name",
                    app,
                    "--resource-group",
                    rg,
                    "--query",
                    "[properties.provisioningState, properties.template.containers[0].image]",
                    "-o",
                    "tsv",
                ],
                text=True,
            ).strip()
            parts = raw.split("\t")
            last_state = parts[0] if len(parts) > 0 else ""
            last_image = parts[1] if len(parts) > 1 else ""
            print(f"Wait {app}: state={last_state} image={last_image}")
            if last_state.lower() == "succeeded" and last_image == expected_image:
                return
        except subprocess.CalledProcessError:
            pass
        time.sleep(interval)
    raise RuntimeError(
        f"Timeout waiting for {app} to update to {expected_image} "
        f"(state={last_state} image={last_image})"
    )


def run_health_check(name, health_cfg):
    if not health_cfg:
        return
    if parse_bool(health_cfg.get("skip", False)):
        print(f"Health check skipped for {name}")
        return

    url = (health_cfg.get("url") or "").strip()
    if not url:
        print(f"Health check skipped for {name} (empty url)")
        return

    expected = int(health_cfg.get("expectedStatus", 200))
    retries = int(health_cfg.get("retries", 12))
    delay = int(health_cfg.get("delaySeconds", 5))

    print(
        f"Health check for {name}: {url} expect={expected} retries={retries}"
    )
    last_err = ""
    for _ in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                status = resp.getcode()
            if status == expected:
                print(f"Health check passed for {name} (status={status})")
                return
            last_err = f"status={status}"
        except Exception as exc:
            last_err = str(exc)
        time.sleep(delay)

    print(f"ERROR: health check failed for {name}: {last_err}", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", default="deploy")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--acr-name", required=True)
    parser.add_argument("--acr-login-server", required=True)
    parser.add_argument("--rg", required=True)
    parser.add_argument("--env", required=True)
    parser.add_argument("--services-file", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(
        f"Action={args.action} tag={args.tag} env={args.env} dryRun={args.dry_run}"
    )

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

    missing_tag = False
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

        if not args.dry_run:
            print(f"Checking tag in repository: {repo}")
            ok = subprocess.check_output(
                [
                    "az",
                    "acr",
                    "repository",
                    "show-tags",
                    "--name",
                    args.acr_name,
                    "--repository",
                    repo,
                    "--query",
                    f"contains(@, '{args.tag}')",
                    "-o",
                    "tsv",
                ],
                text=True,
            ).strip()
            if ok != "true":
                print(
                    f"ERROR: tag {args.tag} not found in repository {repo}",
                    file=sys.stderr,
                )
                print("Available tags (top 20):")
                run_cmd(
                    [
                        "az",
                        "acr",
                        "repository",
                        "show-tags",
                        "--name",
                        args.acr_name,
                        "--repository",
                        repo,
                        "--top",
                        "20",
                    ],
                    args.dry_run,
                )
                missing_tag = True

        deploy_targets.append((name, repo, app, deploy_cfg))

    if missing_tag:
        print(
            f"ERROR: one or more repositories do not contain tag {args.tag}",
            file=sys.stderr,
        )
        return 1

    for name, repo, app, deploy_cfg in deploy_targets:
        env_vars = get_env_vars(deploy_cfg.get("envVars"))
        image = f"{args.acr_login_server}/{repo}:{args.tag}"
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
        if env_vars:
            cmd += ["--set-env-vars"] + env_vars
        run_cmd(cmd, args.dry_run, retries=8, delay_seconds=20)

        if not args.dry_run and args.action == "deploy":
            wait_for_update(app, args.rg, image)
            run_health_check(name, deploy_cfg.get("healthCheck"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
