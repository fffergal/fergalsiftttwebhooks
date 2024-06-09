import sys

import yaml


def main():
    """
    Check overlapping hooks in .pre-commit-config.yaml and requirements are in sync.

    Look for packages in dev-requirements.txt which match the id of the first hook for
    any repo in .pre-commit-config.yaml, then check the requirements version is the same
    as the repo version, removing any leading "v" if necessary.
    """
    # Get the id of each repos first hook in .pre-commit-config.yaml and match it with
    # the repo version.
    with open(".pre-commit-config.yaml") as f:
        data = yaml.load(f, yaml.Loader)
    hook_versions = {
        repo["hooks"][0]["id"]: repo["rev"].lstrip("v")
        for repo in data["repos"]
        if "rev" in repo
    }
    # Get the versions of matching packages from dev-requirements.txt.
    with open("dev-requirements.txt") as f:
        requirements = f.read().splitlines()
    package_versions = {}
    for req in requirements:
        if "==" in req:
            package, version = req.split("==")
            if package in hook_versions:
                package_versions[package] = version
    # Check the versions match.
    good = True
    for package, version in package_versions.items():
        if version != hook_versions[package]:
            good = False
            sys.stderr.write(
                f"Version mismatch for {package}: {version} != {hook_versions[package]}\n"
            )
    if not good:
        sys.exit(1)


if __name__ == "__main__":
    main()
