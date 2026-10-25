#!/usr/bin/env python3
"""Build-only, fail-closed acquisition and installation of reviewed input locks."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import email.parser
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import pwd
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
import zipfile


class LockError(RuntimeError):
    pass


def need(condition, message):
    if not condition:
        raise LockError(message)


def stage(message):
    print("locked-inputs: " + message, file=sys.stderr, flush=True)


def normalized(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def local_name(value):
    need(isinstance(value, str) and value not in {"", ".", ".."}
         and Path(value).name == value and "/" not in value and "\\" not in value,
         "Unsafe input filename: " + repr(value))
    return value


def check_file(path, item):
    need(path.is_file() and not path.is_symlink(), "Missing/nonregular input: " + str(path))
    need(path.stat().st_size == item["bytes"], "Size mismatch: " + str(path))
    need(digest(path) == item["sha256"], "SHA256 mismatch: " + str(path))


def check_environment(observed, expected, label):
    if observed != expected:
        differences = {
            "missing": sorted(set(expected) - set(observed)),
            "extra": sorted(set(observed) - set(expected)),
            "changed": {name: {"expected": expected[name], "observed": observed[name]}
                        for name in sorted(set(expected) & set(observed))
                        if observed[name] != expected[name]},
        }
        raise LockError(label + ": " + json.dumps(differences, sort_keys=True))


def write_receipt(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Receipts are runtime-readable provenance, not writable runtime state.
    path.parent.chmod(0o755)
    value = dict(value, time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    path.chmod(0o644)


def run(argv, *, capture=False, env=None, cwd=None):
    stage("run " + " ".join(str(x) for x in argv))
    result = subprocess.run([str(x) for x in argv], cwd=cwd, env=env, text=True,
                            stdout=subprocess.PIPE if capture else None)
    need(result.returncode == 0, "Command failed (exit %s): %s" % (result.returncode, argv[0]))
    return result.stdout if capture else None


def validate_platform(arch):
    need(sys.platform == "linux", "Installer is only for Linux image build stages")
    actual = {"x86_64": "amd64", "aarch64": "arm64"}.get(platform.machine())
    need(actual == arch, "Native architecture does not match the input lock")
    need(sys.version_info[:2] == (3, 12), "Expected the pinned Python 3.12 base")


def load_lock(path, arch, kind):
    data = json.loads(path.read_text())
    if kind == "apt":
        need(data["schema"] == 2 and data["architecture"] == arch
             and data["stage"] in {"builder", "runtime"},
             "APT lock architecture/stage mismatch")
        need(data["acquisition_policy"] == {
            "mode": "current-signed-official-index-fixed-package-bytes",
            "metadata_may_refresh": True, "allow_package_drift": False,
            "snapshot_fallback": False}, "Unexpected APT acquisition policy")
    else:
        need(data["schema"] == 1 and data["python"] == "3.12"
             and data["platform"] == "linux/" + arch, "Python lock identity mismatch")
        files, sources = data["files"], data["sources"]
        need(len(files) == 30 and len(sources) == 2, "Unexpected Python input closure")
        need(len({local_name(x["filename"]) for x in files + sources}) == 32,
             "Duplicate Python input filename")
        need({normalized(x["name"]): x["version"] for x in sources}
             == {"orthofinder": "3.2", "ete4": "4.4.0"}, "Unexpected source projects")
        for item in files:
            need(item["roles"] in [["build"], ["runtime"]], "Unexpected wheel role")
            need(item["filename"].endswith(".whl"), "Expected a fixed wheel input")
        build = {normalized(x["name"]): x["version"] for x in files if x["roles"] == ["build"]}
        runtime = {normalized(x["name"]): x["version"] for x in files if x["roles"] == ["runtime"]}
        need(len(build) == 6 and len(runtime) == 24, "Unexpected wheel role closure")
        need(data["expected_build_tool_packages"] == build, "Build package lock disagrees")
        need(data["base_pip"]["version"] == "25.0.1", "Unexpected base pip")
        need(data["expected_build_environment_packages"] == dict(build, pip="25.0.1"),
             "Unexpected full build environment")
        runtime.update({normalized(x["name"]): x["version"] for x in sources})
        runtime["pip"] = "25.0.1"
        need(len(runtime) == 27 and data["expected_runtime_packages"] == runtime,
             "Unexpected full runtime environment")
    return data


def dpkg_state():
    output = run(["dpkg-query", "-W", "-f=${Package}\t${Version}\t${Architecture}\t${db:Status-Status}\n"],
                 capture=True)
    result = {}
    for line in output.splitlines():
        name, version, arch, status = line.split("\t")
        need(status == "installed", "Unexpected dpkg state for %s: %s" % (name, status))
        need(name not in result, "Duplicate/multiarch dpkg package: " + name)
        result[name] = {"version": version, "architecture": arch}
    return result


def source_stanzas(repositories, arch):
    need(len(repositories) == 3, "Expected all three signed Debian sources")
    suites = set()
    stanzas = []
    for repo in repositories:
        uri = repo["uri"]
        archive = "debian-security" if repo["suite"] == "bookworm-security" else "debian"
        need(repo["archive"] == archive and uri == "https://deb.debian.org/" + archive + "/",
             "Unexpected official Debian URI")
        need(repo["components"] == ["main"] and repo["signed_by"] == "/usr/share/keyrings/debian-archive-keyring.gpg",
             "Unexpected APT components/keyring")
        need(repo["check_valid_until"] is True and repo["tls_verify_peer"] is True
             and repo["tls_verify_host"] is True, "Invalid Debian security policy")
        suite = repo["suite"]
        need(suite in {"bookworm", "bookworm-updates", "bookworm-security"} and suite not in suites,
             "Unexpected or duplicate Debian suite")
        suites.add(suite)
        need(repo["inrelease_url"] == uri + "dists/" + suite + "/InRelease", "InRelease URL mismatch")
        stanzas.append("\n".join(["Types: deb", "URIs: " + uri, "Suites: " + suite,
                         "Components: main", "Architectures: " + arch,
                         "Signed-By: " + repo["signed_by"], "Check-Valid-Until: yes",
                         "Check-Date: yes"]))
    return "\n\n".join(stanzas) + "\n"


def control_records(lines):
    """Parse Debian control paragraphs without retaining the whole package index."""
    record, key = {}, None
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not line:
            if record:
                yield record
            record, key = {}, None
        elif line[0] in " \t":
            need(key is not None, "Control continuation without a field")
            record[key] += "\n" + line[1:]
        else:
            need(":" in line, "Malformed Debian control field")
            key, value = line.split(":", 1)
            need(key not in record, "Duplicate Debian control field: " + key)
            record[key] = value.strip()
    if record:
        yield record


def verify_package_index(content, release, packages, arch, suite):
    relative = "main/binary-" + arch + "/Packages"
    hashes = {}
    for line in release["SHA256"].splitlines():
        if line.strip():
            sha, size, filename = line.split()
            need(filename not in hashes, "Duplicate signed index path")
            hashes[filename] = (sha, int(size))
    observed = (hashlib.sha256(content).hexdigest(), len(content))
    need(hashes.get(relative) == observed, "Packages content differs from signed InRelease: " + suite)
    expected = {item["name"]: item for item in packages if item["suite"] == suite}
    matched = set()
    for record in control_records(io.StringIO(content.decode("utf-8"))):
        item = expected.get(record.get("Package"))
        if item is None or record.get("Version") != item["version"]:
            continue
        identity = {"Package": item["name"], "Version": item["version"],
                    "Architecture": item["architecture"], "Filename": item["filename"],
                    "Size": str(item["bytes"]), "SHA256": item["sha256"]}
        need(all(record.get(key) == value for key, value in identity.items()),
             "Locked package differs in signed index: " + item["name"])
        need(item["name"] not in matched, "Duplicate locked package in signed index")
        matched.add(item["name"])
    need(matched == set(expected), "Locked packages absent from signed index: "
         + ", ".join(sorted(set(expected) - matched)))
    return {"path": relative, "sha256": observed[0], "bytes": observed[1],
            "matched_locked_packages": sorted(matched)}


def verify_apt_metadata(repositories, packages, arch):
    """Bind fresh signed metadata to immutable package bytes, not a mutable timestamp."""
    directory = Path("/var/lib/apt/lists")
    expected_releases, receipts = set(), []
    for repo in repositories:
        suite = repo["suite"]
        prefix = "deb.debian.org_" + repo["archive"] + "_dists_" + suite
        release_path = directory / (prefix + "_InRelease")
        need(release_path.is_file() and not release_path.is_symlink(), "Missing/nonregular InRelease")
        expected_releases.add(release_path)
        with tempfile.TemporaryDirectory(prefix="taffish-release-", dir="/tmp") as temp:
            cleartext = Path(temp) / "Release"
            status = run(["gpgv", "--keyring", repo["signed_by"], "--status-fd", "1",
                          "--output", cleartext, release_path], capture=True)
            signers = sorted({line.split()[2] for line in status.splitlines()
                              if line.startswith("[GNUPG:] VALIDSIG ")})
            need(signers, "InRelease has no valid trusted signature")
            records = list(control_records(io.StringIO(cleartext.read_text())))
        need(len(records) == 1, "Unexpected Release paragraphs")
        release = records[0]
        need(release.get("Origin") == "Debian" and release.get("Codename") == suite,
             "Wrong signed Debian release identity")
        need(arch in release.get("Architectures", "").split(), "Architecture missing in signed release")
        # APT already checks Date/Valid-Until. The current values are evidence, not frozen inputs.
        # Current bookworm and bookworm-updates omit expiry; security supplies it.
        need("Date" in release and (suite != "bookworm-security" or "Valid-Until" in release),
             "Missing signed release validity metadata")
        base = prefix + "_main_binary-" + arch + "_Packages"
        paths = [directory / (base + suffix) for suffix in ("", ".lz4", ".xz", ".gz")
                 if (directory / (base + suffix)).exists()]
        need(len(paths) == 1 and paths[0].is_file() and not paths[0].is_symlink(),
             "Missing/ambiguous/nonregular APT package index")
        result = subprocess.run(["/usr/lib/apt/apt-helper", "cat-file", str(paths[0])],
                                stdout=subprocess.PIPE)
        need(result.returncode == 0, "Cannot decode verified APT package index")
        index = verify_package_index(result.stdout, release, packages, arch, suite)
        receipts.append({"uri": repo["uri"], "suite": suite,
                         "inrelease_sha256": digest(release_path),
                         "inrelease_bytes": release_path.stat().st_size,
                         "valid_signer_fingerprints": signers, "gpgv_exit_code": 0,
                         "date": release["Date"], "valid_until": release.get("Valid-Until"),
                         "apt_check_date": True, "apt_check_valid_until": True,
                         "packages_index": index})
    need(set(directory.glob("*_InRelease")) == expected_releases, "Unexpected APT InRelease source")
    need(sum(len(r["packages_index"]["matched_locked_packages"]) for r in receipts) == len(packages),
         "Not every locked package was verified against signed metadata")
    return receipts


def verify_debs(directory, packages, inspect):
    by_hash = {item["sha256"]: item for item in packages}
    need(len(by_hash) == len(packages), "Duplicate deb hash in transaction")
    verified = {}
    for path in sorted(directory.glob("*.deb")):
        need(path.is_file() and not path.is_symlink(), "Nonregular deb download")
        item = by_hash.get(digest(path))
        need(item is not None, "Unlisted deb bytes: " + path.name)
        check_file(path, item)
        identity = inspect(path)
        expected = {"Package": item["name"], "Version": item["version"], "Architecture": item["architecture"]}
        need(identity == expected, "Deb metadata mismatch: " + path.name)
        need(item["name"] not in verified, "Duplicate downloaded package")
        verified[item["name"]] = {"version": item["version"], "architecture": item["architecture"],
                                  "sha256": item["sha256"], "bytes": item["bytes"]}
    need(set(verified) == {x["name"] for x in packages}, "Downloaded transaction is incomplete")
    return verified


def deb_metadata(path):
    output = run(["dpkg-deb", "--field", path, "Package", "Version", "Architecture"], capture=True)
    return dict(line.split(": ", 1) for line in output.splitlines())


def apt_install(args):
    need(os.geteuid() == 0, "APT build step requires container root")
    data = load_lock(args.lock, args.arch, "apt")
    need(run(["dpkg", "--print-architecture"], capture=True).strip() == args.arch,
         "dpkg native architecture mismatch")
    need(not run(["dpkg", "--print-foreign-architectures"], capture=True).strip(), "Foreign APT architecture configured")
    packages = data["packages"]
    expected_count = 81 if data["stage"] == "builder" else 42
    need(len(packages) == data["expected_newly_installed_count"] == expected_count
         and data["expected_upgrade_count"] == data["expected_remove_count"] == 0,
         "Unexpected APT transaction size/type")
    before = dpkg_state()
    original_auto = set(run(["apt-mark", "showauto"], capture=True).split())
    for item in data["base_already_installed_roots"]:
        need(item["name"] in before and before[item["name"]]["version"] == item["version"],
             "Base package differs: " + item["name"])
    names = set()
    expected = dict(before)
    for item in packages:
        name = item["name"]
        need(re.fullmatch(r"[a-z0-9][a-z0-9+.-]+", name) and name not in names and name not in before,
             "Unexpected or already installed transaction package: " + name)
        need(item["architecture"] in {args.arch, "all"}, "Wrong deb architecture")
        need(re.fullmatch(r"[A-Za-z0-9.+:~_-]+", item["version"]), "Invalid locked deb version")
        repos = [r for r in data["repositories"] if r["suite"] == item["suite"]]
        need(len(repos) == 1 and item["url"] == repos[0]["uri"] + item["filename"],
             "Locked package source differs from the official repository")
        names.add(name)
        expected[name] = {"version": item["version"], "architecture": item["architecture"]}
    sources = source_stanzas(data["repositories"], args.arch)
    for repo in data["repositories"]:
        need(digest(repo["signed_by"]) == repo["keyring_sha256"], "Base APT keyring differs")
    source_dir = Path("/etc/apt/sources.list.d")
    for old in [Path("/etc/apt/sources.list"), *source_dir.glob("*.list"), *source_dir.glob("*.sources")]:
        if old.exists() or old.is_symlink():
            need(old.is_file() and not old.is_symlink(), "Unexpected APT source file")
            old.unlink()
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "taffish-locked.sources").write_text(sources)
    shutil.rmtree("/var/lib/apt/lists", ignore_errors=False)
    Path("/var/lib/apt/lists").mkdir(mode=0o755)
    common = ["apt-get", "-o", "Acquire::Retries=5", "-o", "Acquire::https::Timeout=120",
              "-o", "Acquire::https::Verify-Peer=true", "-o", "Acquire::https::Verify-Host=true",
              "-o", "Acquire::AllowInsecureRepositories=false", "-o", "APT::Get::AllowUnauthenticated=false",
              "-o", "Acquire::Check-Date=true", "-o", "Acquire::Check-Valid-Until=true"]
    run(common + ["-o", "APT::Update::Error-Mode=any", "update"])
    metadata = verify_apt_metadata(data["repositories"], packages, args.arch)
    install = [item["name"] + "=" + item["version"] for item in packages]
    with tempfile.TemporaryDirectory(prefix="taffish-apt-lock-", dir="/tmp") as temp:
        archives = Path(temp) / "archives"
        Path(temp).chmod(0o755)
        archives.mkdir(mode=0o755)
        partial = archives / "partial"
        partial.mkdir(mode=0o700)
        os.chown(partial, pwd.getpwnam("_apt").pw_uid, 0)
        command = common + ["-o", "Dir::Cache::archives=" + str(archives)]
        run(command + ["--download-only", "install", "-y", "--no-remove", "--no-install-recommends", *install])
        verified = verify_debs(archives, packages, deb_metadata)
        run(command + ["--no-download", "install", "-y", "--no-remove", "--no-install-recommends", *install])
    after = dpkg_state()
    check_environment(after, expected, "APT final package set/version/architecture differs from base + lock")
    roots = set(data["explicit_roots"])
    need(roots <= set(after), "Explicit root missing after locked APT installation")
    desired_auto = ((original_auto | names) - roots) & set(after)
    desired_manual = set(after) - desired_auto
    if desired_auto:
        run(["apt-mark", "auto", *sorted(desired_auto)])
    if desired_manual:
        run(["apt-mark", "manual", *sorted(desired_manual)])
    need(set(run(["apt-mark", "showauto"], capture=True).split()) == desired_auto,
         "APT auto/manual bookkeeping differs")
    shutil.rmtree("/var/lib/apt/lists")
    Path("/var/lib/apt/lists").mkdir(mode=0o755)
    run(["apt-get", "clean"])
    write_receipt(args.receipt, {"kind": "apt", "status": "PASS", "architecture": args.arch,
        "stage": data["stage"], "lock_sha256": digest(args.lock), "base": before, "installed": after,
        "verified_debs": verified,
        "inrelease_sha256": sorted(r["inrelease_sha256"] for r in metadata),
        "verified_repository_metadata": metadata, "auto_packages": sorted(desired_auto)})


def fetch_one(item, directory, reuse):
    name = local_name(item["filename"])
    need(type(item["bytes"]) is int and item["bytes"] > 0
         and re.fullmatch("[0-9a-f]{64}", item["sha256"]), "Invalid locked size/hash")
    url = urlsplit(item["url"])
    need(url.scheme == "https" and url.hostname in {"files.pythonhosted.org", "github.com"}
         and not url.username and not url.password, "Unexpected input URL")
    target = directory / name
    if target.exists() or target.is_symlink():
        check_file(target, item)
        return {"filename": name, "sha256": item["sha256"], "source": "verified existing input"}
    fd, temporary = tempfile.mkstemp(prefix=".download-", dir=directory)
    os.close(fd)
    temporary = Path(temporary)
    try:
        source = reuse / name if reuse is not None else None
        if source is not None and (source.exists() or source.is_symlink()):
            check_file(source, item)
            shutil.copyfile(source, temporary)
        else:
            run(["curl", "--fail", "--location", "--show-error", "--silent", "--proto", "=https",
                 "--proto-redir", "=https", "--connect-timeout", "30", "--max-time", "600",
                 "--retry", "5", "--retry-delay", "2", "--retry-all-errors", "--retry-max-time", "1800",
                 item["url"], "--output", temporary])
        check_file(temporary, item)
        temporary.chmod(0o644)
        # Atomic publication without replacing a concurrently created input.
        os.link(temporary, target)
        return {"filename": name, "sha256": item["sha256"], "source": "verified acquisition"}
    finally:
        temporary.unlink(missing_ok=True)


def fetch_python(args):
    data = load_lock(args.lock, args.arch, "python")
    args.inputs.mkdir(parents=True, exist_ok=True)
    need(not args.inputs.is_symlink(), "Input directory is a symlink")
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(lambda item: fetch_one(item, args.inputs, args.reuse_from),
                                 data["files"] + data["sources"]))
    write_receipt(args.receipt, {"kind": "python-inputs", "status": "PASS", "architecture": args.arch,
                               "lock_sha256": digest(args.lock), "files": receipts})


def pip_env():
    return dict(os.environ, PIP_CONFIG_FILE=os.devnull, PIP_NO_INDEX="1", PIP_NO_CACHE_DIR="1",
                PIP_DISABLE_PIP_VERSION_CHECK="1", PYTHONNOUSERSITE="1")


def installed_python():
    result = {}
    for dist in importlib.metadata.distributions():
        name = normalized(dist.metadata["Name"])
        need(name not in result, "Duplicate installed Python distribution: " + name)
        result[name] = dist.version
    return result


def wheel_identity(path):
    with zipfile.ZipFile(path) as wheel:
        # A wheel may vendor other distributions' metadata below its package.
        # Only its own top-level <distribution>.dist-info/METADATA identifies it.
        members = [name for name in wheel.namelist()
                   if re.fullmatch(r"[^/]+\.dist-info/METADATA", name)]
        need(len(members) == 1, "Expected one wheel distribution metadata")
        metadata = email.parser.BytesParser().parsebytes(wheel.read(members[0]))
        need(metadata["Name"] and metadata["Version"], "Wheel identity is missing")
        return normalized(metadata["Name"]), metadata["Version"]


def check_external_runtime_wheel(path, name, external):
    # Only the two source-built wheels receive newly generated build hashes.
    # A source build cannot silently replace one of the 24 external artifacts.
    if name in external:
        item = external[name]
        need(path.name == item["filename"], "External runtime wheel filename differs: " + name)
        check_file(path, item)


def build_python(args):
    data = load_lock(args.lock, args.arch, "python")
    check_environment(installed_python(), {"pip": "25.0.1"}, "Unexpected base Python environment")
    for item in data["files"] + data["sources"]:
        check_file(args.inputs / local_name(item["filename"]), item)
    tools = [args.inputs / x["filename"] for x in data["files"] if x["roles"] == ["build"]]
    for item in data["files"]:
        need(wheel_identity(args.inputs/item["filename"]) == (normalized(item["name"]), item["version"]),
             "Locked wheel metadata differs")
    run([sys.executable, "-m", "pip", "install", "--no-index", "--no-deps", "--no-cache-dir", *tools], env=pip_env())
    check_environment(installed_python(), data["expected_build_environment_packages"], "Build tool environment differs")
    run([sys.executable, "-m", "pip", "check"], env=pip_env())
    args.wheels.mkdir(parents=True, exist_ok=True)
    need(not args.wheels.is_symlink() and not list(args.wheels.iterdir()), "Output wheelhouse is not empty")
    for item in data["files"]:
        if item["roles"] == ["runtime"]:
            shutil.copyfile(args.inputs/item["filename"], args.wheels/item["filename"])
    for item in data["sources"]:
        run([sys.executable, "-m", "pip", "wheel", "--no-index", "--no-deps", "--no-build-isolation",
             "--no-cache-dir", "--wheel-dir", args.wheels, args.inputs/item["filename"]], env=pip_env())
    paths = sorted(args.wheels.glob("*.whl"))
    need(len(paths) == 26 and len(list(args.wheels.iterdir())) == 26, "Unexpected runtime wheelhouse contents")
    expected = dict(data["expected_runtime_packages"])
    expected.pop("pip")
    external = {normalized(x["name"]): x for x in data["files"] if x["roles"] == ["runtime"]}
    observed, records = {}, []
    for path in paths:
        name, version = wheel_identity(path)
        need(name not in observed, "Duplicate runtime distribution")
        check_external_runtime_wheel(path, name, external)
        observed[name] = version
        records.append({"name": name, "version": version, "filename": path.name,
                        "sha256": digest(path), "bytes": path.stat().st_size})
    check_environment(observed, expected, "Runtime wheel package/version closure differs")
    manifest = {"schema": 1, "architecture": args.arch, "lock_sha256": digest(args.lock),
                "wheels": records, "expected_runtime_packages": data["expected_runtime_packages"]}
    write_receipt(args.wheels/"runtime-wheel-manifest.json", manifest)
    write_receipt(args.receipt, dict(manifest, kind="python-build", status="PASS",
                                    build_environment=installed_python()))


def install_python(args):
    data = load_lock(args.lock, args.arch, "python")
    check_environment(installed_python(), {"pip": "25.0.1"}, "Unexpected runtime base Python environment")
    manifest = json.loads((args.wheels/"runtime-wheel-manifest.json").read_text())
    need(manifest["schema"] == 1 and manifest["architecture"] == args.arch
         and manifest["lock_sha256"] == digest(args.lock), "Runtime wheel manifest identity differs")
    need(manifest["expected_runtime_packages"] == data["expected_runtime_packages"], "Runtime package lock differs")
    records = manifest["wheels"]
    need(len(records) == 26 and len({local_name(x["filename"]) for x in records}) == 26,
         "Unexpected runtime wheel manifest size")
    need({p.name for p in args.wheels.iterdir()} == {x["filename"] for x in records} | {"runtime-wheel-manifest.json"},
         "Unlisted runtime wheelhouse entry")
    expected = dict(data["expected_runtime_packages"])
    expected.pop("pip")
    external = {normalized(x["name"]): x for x in data["files"] if x["roles"] == ["runtime"]}
    observed, paths = {}, []
    for item in records:
        path = args.wheels/item["filename"]
        check_file(path, item)
        name, version = wheel_identity(path)
        need((name, version) == (item["name"], item["version"]) and name not in observed,
             "Runtime wheel metadata differs")
        check_external_runtime_wheel(path, name, external)
        observed[name] = version
        paths.append(path)
    check_environment(observed, expected, "Runtime wheel closure differs")
    run([sys.executable, "-m", "pip", "install", "--no-index", "--no-deps", "--no-cache-dir", *paths], env=pip_env())
    run([sys.executable, "-m", "pip", "check"], env=pip_env())
    check_environment(installed_python(), data["expected_runtime_packages"], "Final Python environment differs")
    write_receipt(args.receipt, {"kind": "python-runtime", "status": "PASS", "architecture": args.arch,
        "lock_sha256": digest(args.lock), "wheel_manifest_sha256": digest(args.wheels/"runtime-wheel-manifest.json"),
        "installed": installed_python()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ["apt", "fetch-python", "build-python", "install-python"]:
        part = sub.add_parser(command)
        part.add_argument("--arch", choices=["amd64", "arm64"], required=True)
        part.add_argument("--lock", type=Path, required=True)
        part.add_argument("--receipt", type=Path, required=True)
        if command in {"fetch-python", "build-python"}:
            part.add_argument("--inputs", type=Path, required=True)
        if command == "fetch-python":
            part.add_argument("--reuse-from", type=Path)
        if command in {"build-python", "install-python"}:
            part.add_argument("--wheels", type=Path, required=True)
    args = parser.parse_args()
    validate_platform(args.arch)
    stage("starting " + args.command)
    {"apt": apt_install, "fetch-python": fetch_python, "build-python": build_python,
     "install-python": install_python}[args.command](args)
    stage("PASS " + args.command)


if __name__ == "__main__":
    try:
        main()
    except (LockError, OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        stage("FAIL " + str(error))
        sys.exit(1)
