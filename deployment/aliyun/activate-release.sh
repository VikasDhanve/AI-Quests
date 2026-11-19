#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
test "$(id -u)" = 0
release="$1"
expected="$2"
[[ "$release" =~ ^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{7,40}$ ]]
[[ "$expected" =~ ^[0-9a-f]{64}$ ]]
base=/srv/apps/ai-quests
test "$(readlink -f "$base")" = "$base"
incoming="$base/incoming/$release.tar.gz"
archive="$base/backups/$release.tar.gz"
target="$base/releases/$release"
backup="$base/backups/$release-config"
test -f "$incoming" && test ! -L "$incoming"
test ! -e "$target"
test ! -e "$archive"
test ! -e "$backup"
test ! -L /etc/nginx/nginx.conf
test ! -L /etc/nginx/conf.d/ai-quests.conf
old=""
if test -e "$base/current" || test -L "$base/current"; then
    test -L "$base/current"
    old=$(readlink -f "$base/current")
    [[ "$old" = "$base/releases/"* ]]
fi
was_running=$(systemctl is-active nginx || true)
was_enabled=$(systemctl is-enabled nginx || true)
mkdir "$backup"
tar -czf "$backup/nginx-before.tar.gz" -C /etc nginx
if test -f /etc/nginx/conf.d/ai-quests.conf; then
    cp -p /etc/nginx/conf.d/ai-quests.conf "$backup/site-before.conf"
fi
cp -p /etc/nginx/nginx.conf "$backup/nginx-before.conf"
mv -T "$incoming" "$archive"
chown root:root "$archive"
chmod 600 "$archive"
printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --status
mkdir "$target"
python3 - "$archive" "$target" <<'PY'
from pathlib import Path, PurePosixPath
import hashlib,json,shutil,sys,tarfile
archive,target=sys.argv[1],Path(sys.argv[2])
with tarfile.open(archive,"r:gz") as tar:
    seen=set()
    for member in tar:
        name=PurePosixPath(member.name)
        assert not name.is_absolute() and ".." not in name.parts, member.name
        assert member.isfile() and member.name not in seen, member.name
        assert member.name=="release-manifest.json" or member.name in ("ops/nginx.conf","ops/ai-quests.conf") or member.name.startswith("public/"), member.name
        seen.add(member.name)
        destination=target.joinpath(*name.parts)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with tar.extractfile(member) as source,destination.open("xb") as output:
            shutil.copyfileobj(source,output,1024*1024)
manifest=json.loads((target/"release-manifest.json").read_text())
expected=set()
for row in manifest["files"]:
    p=target/"public"/row["path"]
    assert p.is_file() and not p.is_symlink() and p.stat().st_size==row["bytes"],row["path"]
    digest=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):digest.update(block)
    assert digest.hexdigest()==row["sha256"],row["path"]
    expected.add(row["path"])
actual=set(p.relative_to(target/"public").as_posix() for p in (target/"public").rglob("*") if p.is_file())
assert actual==expected
print(json.dumps({"release":manifest["release"],"verified_files":len(expected),"bytes":manifest["total_bytes"]}))
PY
chmod -R u=rwX,go=rX "$target"
rollback() {
    status=$?
    trap - ERR
    cp -p "$backup/nginx-before.conf" /etc/nginx/nginx.conf
    if test -f "$backup/site-before.conf"; then
        cp -p "$backup/site-before.conf" /etc/nginx/conf.d/ai-quests.conf
    elif test -f /etc/nginx/conf.d/ai-quests.conf; then
        mv -T /etc/nginx/conf.d/ai-quests.conf "$backup/failed-site.conf"
    fi
    if test -L "$base/current"; then
        mv -T "$base/current" "$backup/failed-current"
    fi
    if test -n "$old"; then ln -s "$old" "$base/current"; fi
    if test "$was_running" = active; then
        nginx -t && systemctl reload nginx
    else
        systemctl stop nginx || true
    fi
    if test "$was_enabled" != enabled; then systemctl disable nginx || true; fi
    printf 'Activation failed; original configuration restored.\n' >&2
    exit "$status"
}
trap rollback ERR
install -m 644 "$target/ops/nginx.conf" /etc/nginx/nginx.conf
install -m 644 "$target/ops/ai-quests.conf" /etc/nginx/conf.d/ai-quests.conf
ln -s "$target" "$base/.current-$release"
mv -Tf "$base/.current-$release" "$base/current"
nginx -t
if test "$was_running" = active; then
    systemctl reload nginx
else
    systemctl enable --now nginx
fi
curl --noproxy '*' -fsS -H 'Host: 182.92.231.54' http://127.0.0.1/ai-quests/intl/zh_cn/ >/dev/null
trap - ERR
printf '%s\n' "$release" > "$base/ops/current-release"
printf '%s\n' "$expected" > "$base/ops/current-package-sha256"
printf 'Activated %s\n' "$release"
systemctl is-active nginx
systemctl is-enabled nginx
ss -lntp | grep -E ':80[[:space:]]'