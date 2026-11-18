#!/usr/bin/env bash
# 下載某個 GitHub skill 的資料夾（SKILL.md 所在目錄）到隔離的暫存目錄，
# 並印出檔案清單與 SKILL.md 內容供審查。不會執行任何下載下來的檔案。
# 用法：fetch_skill.sh <owner/repo> <path/to/SKILL.md> [dest_root]
# 只用 git sparse clone（公開 repo 不需任何 token）。
set -euo pipefail

REPO="${1:?owner/repo}"
SKILL_PATH="${2:?path to SKILL.md}"
DEST_ROOT="${3:-${TMPDIR:-/tmp}/fetched-skills}"

DIR=$(dirname "$SKILL_PATH"); [ "$DIR" = "." ] && DIR=""
NAME=$(basename "${DIR:-${REPO#*/}}")
DEST="$DEST_ROOT/${REPO//\//__}__${NAME}"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# 淺層 + 稀疏 clone：只抓該 skill 目錄的檔案
git clone -q --depth 1 --filter=blob:none --no-checkout "https://github.com/$REPO.git" "$WORK/repo"
git -C "$WORK/repo" sparse-checkout set --no-cone "/${DIR:+$DIR/}*" >/dev/null
git -C "$WORK/repo" -c core.hooksPath=/dev/null checkout -q
SHA=$(git -C "$WORK/repo" rev-parse HEAD)

rm -rf "$DEST"; mkdir -p "$DEST"
cp -r "$WORK/repo/${DIR:-.}/." "$DEST/"
rm -rf "$DEST/.git"
# 根目錄的 LICENSE 一起帶上（若 skill 目錄本身沒有）
for f in LICENSE LICENSE.md LICENSE.txt; do
  if [ ! -e "$DEST/$f" ]; then
    curl -fsSL --max-time 15 "https://raw.githubusercontent.com/$REPO/$SHA/$f" -o "$DEST/$f" 2>/dev/null && break || rm -f "$DEST/$f"
  fi
done

# 記錄來源，方便日後追溯 / 更新
printf 'source: https://github.com/%s/tree/%s/%s\ncommit: %s\nfetched: %s\n' \
  "$REPO" "$SHA" "$DIR" "$SHA" "$(date -u +%FT%TZ)" > "$DEST/.source"

echo "== saved to: $DEST"
echo "== files:"; (cd "$DEST" && find . -type f | sort)
echo "== SKILL.md:"; cat "$DEST/SKILL.md"
