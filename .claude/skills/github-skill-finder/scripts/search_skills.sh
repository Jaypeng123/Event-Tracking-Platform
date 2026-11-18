#!/usr/bin/env bash
# 在 GitHub 上搜尋 SKILL.md，輸出候選清單（TSV，依星數排序）：
#   stars  updated  repo  path  description
# 用法：search_skills.sh <關鍵字...>        例：search_skills.sh react testing
# 環境變數：LIMIT（預設 15）
# 需求：jq，以及 gh CLI（已登入）或 GITHUB_TOKEN —— GitHub 的 code search 必須驗證。
# 只用到 search API + raw.githubusercontent.com，所以不需要對目標 repo 有任何權限。
set -euo pipefail

if [ $# -eq 0 ]; then
  echo "usage: $0 <keywords...>" >&2
  exit 1
fi
KEYWORDS="$*"
LIMIT="${LIMIT:-15}"

search() { # search <code|repositories> <query> <per_page>
  if command -v gh >/dev/null 2>&1; then
    gh api -X GET "search/$1" -f q="$2" -f per_page="$3"
  else
    : "${GITHUB_TOKEN:?need gh CLI or GITHUB_TOKEN (GitHub code search requires auth)}"
    curl -fsSL -G -H "Authorization: Bearer $GITHUB_TOKEN" \
      -H "Accept: application/vnd.github+json" \
      --data-urlencode "q=$2" --data-urlencode "per_page=$3" \
      "https://api.github.com/search/$1"
  fi
}

# 1) 依檔名搜尋 SKILL.md
hits=$(search code "filename:SKILL.md $KEYWORDS" "$LIMIT" \
  | jq -r '.items[] | [.repository.full_name, .path] | @tsv' | sort -u)

if [ -z "$hits" ]; then
  echo "no results for: $KEYWORDS" >&2
  exit 0
fi

# 2) 一次查回所有 repo 的星數與更新時間
repo_q=$(cut -f1 <<< "$hits" | sort -u | sed 's/^/repo:/' | paste -sd' ')
declare -A meta
while IFS=$'\t' read -r r s u; do meta[$r]="$s"$'\t'"$u"; done < <(
  search repositories "$repo_q" 100 \
    | jq -r '.items[] | [.full_name, .stargazers_count, .pushed_at[:10]] | @tsv')

# 3) 從 raw.githubusercontent.com 讀 SKILL.md frontmatter 的 description
printf 'stars\tupdated\trepo\tpath\tdescription\n'
while IFS=$'\t' read -r repo path; do
  desc=$(curl -fsSL --max-time 15 "https://raw.githubusercontent.com/$repo/HEAD/$path" 2>/dev/null \
    | awk '
        /^---[ \t]*$/ { n++; if (n==2) exit; next }
        n==1 && /^description:/ { sub(/^description:[ \t]*/, ""); d=$0; grab=1; next }
        n==1 && grab && /^[ \t]+/ { sub(/^[ \t]+/, ""); d=d " " $0; next }
        n==1 && grab { exit }
        END { gsub(/^[>|-]+ */, "", d); print d }' \
    | tr '\t' ' ' | cut -c1-200 || true)
  printf '%s\t%s\t%s\t%s\n' "${meta[$repo]:-?	?}" "$repo" "$path" "${desc:--}"
done <<< "$hits" | sort -t$'\t' -k1,1nr
