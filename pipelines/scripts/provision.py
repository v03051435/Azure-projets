#!/usr/bin/env python3
import argparse
import json
import re
import shlex
import subprocess
import sys


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


def run(cmd, dry_run):
    print(f"CMD: {join_cmd(cmd)}")
    if dry_run:
        return
    subprocess.run(cmd, check=True)


def run_capture(cmd, dry_run):
    print(f"CMD: {join_cmd(cmd)}")
    if dry_run:
        return ""
    return subprocess.check_output(cmd, text=True).strip()


def get_env_vars(env_vars):
    if not env_vars:
        return []
    if isinstance(env_vars, list):
        return env_vars
    return shlex.split(str(env_vars))


def env_name_from_id(env_id):
    if not env_id:
        return ""
    match = re.search(r"/managedEnvironments/([^/]+)$", env_id)
    return match.group(1) if match else ""


def try_get_env_id(app_name, rg, dry_run):
    if dry_run:
        return ""
    try:
        return run_capture(
            [
                "az",
                "containerapp",
                "show",
                "--name",
                app_name,
                "--resource-group",
                rg,
                "--query",
                "properties.managedEnvironmentId",
                "-o",
                "tsv",
            ],
            dry_run,
        )
    except subprocess.CalledProcessError:
        return ""


def get_acr_id(acr_name, dry_run):
    return run_capture(
        [
            "az",
            "acr",
            "show",
            "--name",
            acr_name,
            "--query",
            "id",
            "-o",
            "tsv",
        ],
        dry_run,
    )


def get_principal_id(app_name, rg, dry_run):
    return run_capture(
        [
            "az",
            "containerapp",
            "show",
            "--name",
            app_name,
            "--resource-group",
            rg,
            "--query",
            "identity.principalId",
            "-o",
            "tsv",
        ],
        dry_run,
    )


def ensure_identity(app_name, rg, dry_run):
    run(
        [
            "az",
            "containerapp",
            "identity",
            "assign",
            "--system-assigned",
            "--name",
            app_name,
            "--resource-group",
            rg,
        ],
        dry_run,
    )


def ensure_registry_identity(app_name, rg, acr_login_server, dry_run):
    run(
        [
            "az",
            "containerapp",
            "registry",
            "set",
            "--name",
            app_name,
            "--resource-group",
            rg,
            "--server",
            acr_login_server,
            "--identity",
            "system",
        ],
        dry_run,
    )


def ensure_acr_pull(principal_id, acr_id, dry_run):
    cmd = [
        "az",
        "role",
        "assignment",
        "create",
        "--assignee-object-id",
        principal_id,
        "--assignee-principal-type",
        "ServicePrincipal",
        "--role",
        "acrpull",
        "--scope",
        acr_id,
    ]
    print(f"CMD: {join_cmd(cmd)}")
    if dry_run:
        return
    result = subprocess.run(
        cmd, text=True, capture_output=True
    )
    if result.returncode == 0:
        return
    stderr = (result.stderr or "").lower()
    if "roleassignmentexists" in stderr or "already exists" in stderr:
        return
    raise subprocess.CalledProcessError(
        result.returncode, cmd, output=result.stdout, stderr=result.stderr
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--registry-server", "--acr-login-server", dest="registry_server", required=True)
    parser.add_argument("--acr-name", default="")
    parser.add_argument("--registry-username", default="")
    parser.add_argument("--registry-password", default="")
    parser.add_argument("--rg", required=True)
    parser.add_argument("--env", required=True)
    parser.add_argument("--services-file", required=True)
    parser.add_argument("--env-name", default="")
    parser.add_argument("--dry-run", action="store_true")
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
        print("No services found.")
        return 0

    env_name = (args.env_name or "").strip()
    if not env_name:
        for _, svc in services.items():
            deploy_cfg = (svc.get("deploy") or {}).get(args.env)
            if not deploy_cfg or parse_bool(deploy_cfg.get("skip", False)):
                continue
            app = (deploy_cfg.get("appName") or "").strip()
            if not app:
                continue
            env_id = try_get_env_id(app, args.rg, args.dry_run)
            env_name = env_name_from_id(env_id)
            if env_name:
                print(f"Resolved environment from {app}: {env_name}")
                break

    if not env_name:
        print(
            "ERROR: Could not resolve Container Apps environment name.",
            file=sys.stderr,
        )
        print(
            "Provide --env-name or ensure at least one existing app is deployed.",
            file=sys.stderr,
        )
        return 1

    to_create = []
    deploy_targets = []
    for name, svc in services.items():
        repo = (svc.get("repo") or "").strip()
        if not repo or parse_bool(svc.get("skip", False)):
            continue
        deploy_cfg = (svc.get("deploy") or {}).get(args.env)
        if not deploy_cfg or parse_bool(deploy_cfg.get("skip", False)):
            continue
        app = (deploy_cfg.get("appName") or "").strip()
        if not app:
            print(
                f"ERROR: {name} missing appName for env={args.env}",
                file=sys.stderr,
            )
            return 1
        deploy_targets.append((name, repo, app, deploy_cfg))
        env_id = try_get_env_id(app, args.rg, args.dry_run)
        if env_id:
            print(f"Exists: {app}")
        else:
            to_create.append((name, repo, app, deploy_cfg))

    if not to_create:
        print("No new Container Apps to create.")

    acr_id = ""
    if args.acr_name:
        acr_id = get_acr_id(args.acr_name, args.dry_run)
        if not args.dry_run and not acr_id:
            print(
                "ERROR: Unable to resolve ACR resource id.",
                file=sys.stderr,
            )
            return 1

    for name, repo, app, deploy_cfg in to_create:
        env_vars = get_env_vars(deploy_cfg.get("envVars"))
        registry_host = args.registry_server.split("/")[0]
        cmd = [
            "az",
            "containerapp",
            "create",
            "--name",
            app,
            "--resource-group",
            args.rg,
            "--environment",
            env_name,
            "--image",
            f"{args.registry_server}/{repo}:{args.tag}",
            "--ingress",
            "external",
            "--target-port",
            "8080",
            "--revisions-mode",
            "single",
            "--system-assigned",
        ]
        if args.registry_username and args.registry_password:
            cmd += [
                "--registry-server",
                registry_host,
                "--registry-username",
                args.registry_username,
                "--registry-password",
                args.registry_password,
            ]
        else:
            cmd += [
                "--registry-server",
                args.registry_server,
                "--registry-identity",
                "system",
            ]
        if env_vars:
            cmd += ["--env-vars"] + env_vars
        print(f"Creating {name} -> {app}")
        run(cmd, args.dry_run)

    for name, repo, app, deploy_cfg in to_create:
        if args.dry_run:
            continue
        if not (args.registry_username and args.registry_password):
            ensure_identity(app, args.rg, args.dry_run)
            ensure_registry_identity(app, args.rg, args.registry_server.split("/")[0], args.dry_run)
            principal_id = get_principal_id(app, args.rg, args.dry_run)
            if principal_id and acr_id:
                ensure_acr_pull(principal_id, acr_id, args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
