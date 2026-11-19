from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess, tarfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
release = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + commit[:7]
out = HERE / "artifacts" / release
out.mkdir(parents=True, exist_ok=False)
files = []
for file in sorted(PUBLIC.rglob("*")):
    if file.is_symlink():
        raise RuntimeError("Unexpected symlink: " + str(file))
    if not file.is_file():
        continue
    relative = file.relative_to(PUBLIC).as_posix()
    if any(part.startswith(".") for part in file.relative_to(PUBLIC).parts):
        raise RuntimeError("Unexpected hidden file: " + relative)
    with file.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    files.append({"path": relative, "bytes": file.stat().st_size, "sha256": digest})
assert len(files) > 1700 and sum(f["bytes"] for f in files) > 1_000_000_000
assert (PUBLIC / "ai-quests/intl/zh_cn/index.html").is_file()
official = json.loads((ROOT / "reports/manifest.json").read_text("utf-8"))
mods = {row["path"]: row for row in json.loads((ROOT / "reports/local-modifications.json").read_text("utf-8"))}
for row in official.values():
    if row.get("status") != "ok":
        continue
    original = ROOT / "upstream-text" / row["path"]
    if not original.is_file():
        original = PUBLIC / row["path"]
    with original.open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == row["sha256"], row["path"]
for relative, row in mods.items():
    with (PUBLIC / relative).open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == row["local_sha256"], relative
metadata = {"release": release, "commit": commit, "files": files, "file_count": len(files), "total_bytes": sum(f["bytes"] for f in files)}
manifest = out / "release-manifest.json"
manifest.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), "utf-8")
archive = out / (release + ".tar.gz")
with tarfile.open(archive, "w:gz", compresslevel=1, dereference=False) as tar:
    tar.add(manifest, arcname="release-manifest.json")
    for row in files:
        tar.add(PUBLIC / row["path"], arcname="public/" + row["path"], recursive=False)
    for name in ["nginx.conf", "ai-quests.conf"]:
        tar.add(HERE / name, arcname="ops/" + name, recursive=False)
with archive.open("rb") as stream:
    digest = hashlib.file_digest(stream, "sha256").hexdigest()
summary = {"release": release, "commit": commit, "archive": str(archive), "archive_bytes": archive.stat().st_size, "sha256": digest, "file_count": len(files), "total_bytes": metadata["total_bytes"], "official_hashes_verified": sum(row.get("status") == "ok" for row in official.values()), "modified_hashes_verified": len(mods)}
(out / "package.json").write_text(json.dumps(summary, indent=2), "utf-8")
(HERE / "artifacts/latest-package.json").write_text(json.dumps(summary, indent=2), "utf-8")
print(json.dumps(summary, ensure_ascii=False))