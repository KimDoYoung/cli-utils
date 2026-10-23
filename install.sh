#!/usr/bin/env bash
# cli-utils installer
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"

# 색상 (터미널일 때만)
if [[ -t 1 ]]; then
  C_RESET=$'\033[0m'; C_BOLD=$'\033[1m'
  C_GREEN=$'\033[32m'; C_RED=$'\033[31m'; C_YELLOW=$'\033[33m'; C_CYAN=$'\033[36m'; C_DIM=$'\033[2m'
else
  C_RESET=""; C_BOLD=""; C_GREEN=""; C_RED=""; C_YELLOW=""; C_CYAN=""; C_DIM=""
fi

# ------------------------------------------------------------
# 유틸
# ------------------------------------------------------------
die() { echo "${C_RED}✗ $*${C_RESET}" >&2; exit 1; }

have_uv() { command -v uv >/dev/null 2>&1; }

require_uv() {
  have_uv || { echo "${C_RED}✗ uv 가 설치되어 있지 않습니다. https://docs.astral.sh/uv/${C_RESET}" >&2; return 1; }
}

pause() {
  echo
  read -r -p "${C_DIM}계속하려면 Enter...${C_RESET}" _ || true
}

confirm() {
  local msg="$1"
  local ans
  read -r -p "$msg [y/N]: " ans
  [[ "$ans" =~ ^[yY]$ ]]
}

list_projects() {
  find "$ROOT_DIR" -mindepth 2 -maxdepth 2 -name pyproject.toml -printf '%h\n' 2>/dev/null \
    | sort \
    | while read -r p; do basename "$p"; done
}

build_index_map() {
  local i=1
  while read -r p; do
    echo "$p $i"
    i=$((i+1))
  done < <(list_projects)
}

project_path() { echo "$ROOT_DIR/$1"; }

project_name() {
  local dir; dir="$(project_path "$1")"
  local n
  n=$(awk '
    BEGIN { in_proj=0 }
    /^\[project\]/ { in_proj=1; next }
    /^\[/ { in_proj=0 }
    in_proj && /^[[:space:]]*name[[:space:]]*=/ {
      sub(/^[[:space:]]*name[[:space:]]*=[[:space:]]*["'\''"]/, "")
      sub(/["'\''"][[:space:]]*$/, "")
      print
      exit
    }
  ' "$dir/pyproject.toml" 2>/dev/null)
  echo "${n:-$1}"
}

project_version() {
  local dir; dir="$(project_path "$1")"
  local v
  v=$(awk '
    BEGIN { in_proj=0 }
    /^\[project\]/ { in_proj=1; next }
    /^\[/ { in_proj=0 }
    in_proj && /^[[:space:]]*version[[:space:]]*=/ {
      sub(/^[[:space:]]*version[[:space:]]*=[[:space:]]*["'\''"]/, "")
      sub(/["'\''"][[:space:]]*$/, "")
      print
      exit
    }
  ' "$dir/pyproject.toml" 2>/dev/null)
  echo "${v:-?}"
}

project_description() {
  local dir; dir="$(project_path "$1")"
  awk '
    BEGIN { in_proj=0 }
    /^\[project\]/ { in_proj=1; next }
    /^\[/ { in_proj=0 }
    in_proj && /^[[:space:]]*description[[:space:]]*=/ {
      sub(/^[[:space:]]*description[[:space:]]*=[[:space:]]*["'\''"]/, "")
      sub(/["'\''"][[:space:]]*$/, "")
      print
      exit
    }
  ' "$dir/pyproject.toml" 2>/dev/null
}

project_scripts() {
  local dir; dir="$(project_path "$1")"
  awk '
    BEGIN { in_scripts=0 }
    /^\[project\.scripts\]/ { in_scripts=1; next }
    /^\[/ { in_scripts=0 }
    in_scripts && /=/ {
      sub(/^[[:space:]]*/, "")
      split($0, a, "=")
      gsub(/[[:space:]]/, "", a[1])
      if (a[1] != "") print a[1]
    }
  ' "$dir/pyproject.toml" 2>/dev/null
}

installed_names() {
  uv tool list 2>/dev/null | awk '/^[a-zA-Z0-9_.-]+ v[0-9]/{print $1}'
}

is_installed() {
  local name="$1"
  installed_names | grep -qx "$name" 2>/dev/null
}

installed_version() {
  local name="$1"
  uv tool list 2>/dev/null | awk -v n="$name" '$1==n && $2 ~ /^v/ {print substr($2,2); exit}'
}

# ------------------------------------------------------------
# 표시
# ------------------------------------------------------------
print_header() {
  echo
  echo "${C_CYAN}${C_BOLD}================================${C_RESET}"
  echo "${C_CYAN}${C_BOLD}  cli-utility installer${C_RESET}"
  echo "${C_CYAN}${C_BOLD}================================${C_RESET}"
  echo "${C_DIM}  root: $ROOT_DIR${C_RESET}"
}

print_menu() {
  echo
  echo "  1. 설치 현황 보기"
  echo "  2. 모두 재설치"
  echo "  3. 설치"
  echo "  4. 재설치"
  echo "  5. 제거"
  echo "  6. 새로 추가된 것만 설치"
  echo "  7. 손상/누락 점검 (doctor)"
  echo "  8. 목록 상세 보기"
  echo "  9. uv / python 환경 점검"
  echo "  ----------------------------------------"
  echo "  0. 도움말"
  echo "  99. 종료"
  echo
}

print_indexed() {
  local map; map="$(build_index_map)"
  for p in "$@"; do
    local name ver status iv scripts desc gidx
    name="$(project_name "$p")"
    ver="$(project_version "$p")"
    scripts="$(project_scripts "$p" | paste -sd',' -)"
    desc="$(project_description "$p")"
    gidx="$(echo "$map" | awk -v k="$p" '$1==k{print $2}')"

    if is_installed "$name"; then
      iv="$(installed_version "$name")"
      status="${C_GREEN}[설치됨 v${iv:-?}]${C_RESET}"
    else
      status="${C_YELLOW}[미설치]${C_RESET}"
    fi

    printf "  #%-2s %-20s %s\n" "$gidx" "$name" "$status"
    printf "        ${C_DIM}cmd: %-24s ver: v%s${C_RESET}\n" "${scripts:-—}" "$ver"
    if [[ -n "$desc" ]]; then
      printf "        ${C_DIM}%s${C_RESET}\n" "$desc"
    fi
  done
}

# ------------------------------------------------------------
# 도움말
# ------------------------------------------------------------
action_help() {
  echo
  echo "${C_BOLD}=========================================================${C_RESET}"
  echo "${C_BOLD}  도움말${C_RESET}"
  echo "${C_BOLD}=========================================================${C_RESET}"
  echo
  echo "  ${C_BOLD}[메뉴 설명]${C_RESET}"
  echo
  printf "  %-4s %-22s %s\n" "번호" "이름" "설명"
  printf "  %-4s %-22s %s\n" "----" "----------------------" "--------------------------------------------"
  printf "  %-4s %-22s %s\n" "1"  "설치 현황 보기"        "각 프로젝트의 선언버전/설치버전/스크립트 목록 표시"
  printf "  %-4s %-22s %s\n" "2"  "모두 재설치"            "모든 하위 프로젝트를 강제 재설치 (실행 전 확인)"
  printf "  %-4s %-22s %s\n" "3"  "설치"                  "미설치 프로젝트만 골라서 설치 (없으면 전체 폴백)"
  printf "  %-4s %-22s %s\n" "4"  "재설치"                "설치된 프로젝트만 골라서 재설치 (없으면 전체 폴백)"
  printf "  %-4s %-22s %s\n" "5"  "제거"                  "설치된 프로젝트를 골라 제거 (실행 전 확인)"
  printf "  %-4s %-22s %s\n" "6"  "새로 추가된 것만 설치" "pyproject.toml 은 있는데 미설치인 것 자동 설치"
  printf "  %-4s %-22s %s\n" "7"  "손상/누락 점검"        "[project.scripts] 커맨드가 PATH 에서 실행되는지 점검"
  printf "  %-4s %-22s %s\n" "8"  "목록 상세 보기"        "각 프로젝트의 name/version/scripts/path 표시"
  printf "  %-4s %-22s %s\n" "9"  "환경 점검"              "uv/python 버전, PATH, uv tool dir 표시"
  printf "  %-4s %-22s %s\n" "0"  "도움말"                "이 화면"
  printf "  %-4s %-22s %s\n" "99" "종료"                  "프로그램 종료"
  echo
  echo "  ${C_BOLD}[현재 폴더 목록]${C_RESET}"
  echo "  ${C_DIM}root: $ROOT_DIR${C_RESET}"
  echo

  local any=0 i=1
  while read -r p; do
    any=1
    local name ver iv scripts mark
    name="$(project_name "$p")"; ver="$(project_version "$p")"
    scripts="$(project_scripts "$p" | paste -sd',' -)"
    if is_installed "$name"; then
      iv="$(installed_version "$name")"
      mark="${C_GREEN}●${C_RESET}"
    else
      iv="-"
      mark="${C_DIM}○${C_RESET}"
    fi
    printf "  #%-2s %s %-20s v%-8s installed:%-8s cmd:%s\n" \
      "$i" "$mark" "$p" "$ver" "$iv" "${scripts:-—}"
    i=$((i+1))
  done < <(list_projects)
  [[ $any -eq 0 ]] && echo "  ${C_YELLOW}(하위에 pyproject.toml 을 가진 프로젝트가 없습니다)${C_RESET}"

  echo
  echo "  ${C_DIM}● 설치됨   ○ 미설치${C_RESET}"
}

# ------------------------------------------------------------
# 액션
# ------------------------------------------------------------
action_status() {
  require_uv || return 1
  echo
  echo "${C_BOLD}[설치 현황]${C_RESET}"
  printf "  %-4s %-20s %-10s %-10s %s\n" "" "PROJECT" "DECLARED" "INSTALLED" "SCRIPTS"
  printf "  %-4s %-20s %-10s %-10s %s\n" "----" "--------------------" "----------" "----------" "-------"
  local i=1
  while read -r p; do
    local name ver iv scripts
    name="$(project_name "$p")"; ver="$(project_version "$p")"
    if is_installed "$name"; then iv="$(installed_version "$name")"; else iv="-"; fi
    scripts="$(project_scripts "$p" | paste -sd',' -)"
    printf "  #%-2s  %-20s %-10s %-10s %s\n" "$i" "$p" "v$ver" "$iv" "${scripts:-—}"
    i=$((i+1))
  done < <(list_projects)
}

select_projects() {
  local mode="$1"

  local all=()
  while read -r p; do all+=("$p"); done < <(list_projects)
  if [[ ${#all[@]} -eq 0 ]]; then
    echo "${C_RED}하위에 pyproject.toml 을 가진 프로젝트가 없습니다.${C_RESET}" >&2
    return 1
  fi

  local pool=()
  local p name
  for p in "${all[@]}"; do
    name="$(project_name "$p")"
    case "$mode" in
      install)   is_installed "$name" || pool+=("$p") ;;
      reinstall) is_installed "$name" && pool+=("$p") ;;
      uninstall) is_installed "$name" && pool+=("$p") ;;
    esac
  done

  if [[ ${#pool[@]} -eq 0 ]]; then
    if [[ "$mode" == "uninstall" ]]; then
      echo "${C_YELLOW}제거할 설치된 프로젝트가 없습니다.${C_RESET}" >&2
      return 1
    fi
    pool=("${all[@]}")
    echo "${C_YELLOW}대상이 비어 있어 전체 목록으로 진행합니다.${C_RESET}" >&2
  fi

  echo >&2
  echo "${C_BOLD}대상:${C_RESET}" >&2
  echo "${C_DIM}  #번호는 '0. 도움말' 의 목록 번호와 동일합니다.${C_RESET}" >&2
  echo >&2
  print_indexed "${pool[@]}" >&2

  echo >&2
  local label
  case "$mode" in
    install)   label="설치" ;;
    reinstall) label="재설치" ;;
    uninstall) label="제거" ;;
  esac
  
  local choice
  read -r -p "선택 (#번호 쉼표: 1,3,5 / a=전체 / 0=취소) → ${label}: " choice >&2

  [[ "$choice" == "0" || -z "$choice" ]] && return 1

  local selected=()
  if [[ "$choice" == "a" || "$choice" == "A" ]]; then
    selected=("${pool[@]}")
  else
    IFS=',' read -r -a nums <<< "$choice"
    local n idx pick allowed
    for n in "${nums[@]}"; do
      n="$(echo "$n" | tr -d ' ')"
      [[ "$n" =~ ^[0-9]+$ ]] || continue
      idx=$((n-1))
      [[ $idx -ge 0 && $idx -lt ${#all[@]} ]] || continue
      pick="${all[$idx]}"
      allowed=0
      for p in "${pool[@]}"; do
        [[ "$p" == "$pick" ]] && { allowed=1; break; }
      done
      if [[ $allowed -eq 1 ]]; then
        selected+=("$pick")
      else
        echo "${C_YELLOW}  #$n ($(project_name "$pick")) 은(는) 현재 모드 대상이 아닙니다. skip.${C_RESET}" >&2
      fi
    done
  fi

  [[ ${#selected[@]} -eq 0 ]] && { echo "${C_YELLOW}선택 없음.${C_RESET}" >&2; return 1; }
  printf '%s\n' "${selected[@]}"
  return 0
}

do_install_one() {
  local p="$1"
  local name; name="$(project_name "$p")"
  local dir;  dir="$(project_path "$p")"
  if is_installed "$name"; then
    echo "${C_DIM}… skip (이미 설치됨): $p${C_RESET}"
    return 0
  fi
  echo "${C_CYAN}▶ install: $p${C_RESET}"
  echo "${C_DIM}  $ (cd $dir && uv tool install .)${C_RESET}"
  ( cd "$dir" && uv tool install . ) || { echo "${C_RED}✗ 실패: $p${C_RESET}"; return 1; }
}

do_reinstall_one() {
  local p="$1"
  local dir; dir="$(project_path "$p")"
  echo "${C_CYAN}▶ reinstall: $p${C_RESET}"
  echo "${C_DIM}  $ (cd $dir && uv tool install --reinstall .)${C_RESET}"
  ( cd "$dir" && uv tool install --reinstall . ) || { echo "${C_RED}✗ 실패: $p${C_RESET}"; return 1; }
}

do_uninstall_one() {
  local p="$1"
  local name; name="$(project_name "$p")"
  echo "${C_CYAN}▶ uninstall: $name${C_RESET}"
  echo "${C_DIM}  $ uv tool uninstall $name${C_RESET}"
  uv tool uninstall "$name" || { echo "${C_RED}✗ 실패: $name${C_RESET}"; return 1; }
}

action_bulk() {
  local mode="$1"
  require_uv || return 1
  local selected
  selected="$(select_projects "$mode")" || return 0

  if [[ "$mode" == "uninstall" ]]; then
    local cnt
    cnt="$(echo "$selected" | grep -c . || true)"
    if ! confirm "${C_YELLOW}${cnt}개를 제거합니다. 진행할까요?${C_RESET}"; then
      echo "${C_DIM}취소됨.${C_RESET}"
      return 0
    fi
  fi

  local ok=0 fail=0
  while read -r p; do
    [[ -z "$p" ]] && continue
    case "$mode" in
      install)   do_install_one   "$p" && ok=$((ok+1)) || fail=$((fail+1)) ;;
      reinstall) do_reinstall_one "$p" && ok=$((ok+1)) || fail=$((fail+1)) ;;
      uninstall) do_uninstall_one "$p" && ok=$((ok+1)) || fail=$((fail+1)) ;;
    esac
  done <<< "$selected"

  echo
  echo "${C_BOLD}[요약]${C_RESET} 성공 $ok / 실패 $fail"
  [[ $fail -eq 0 ]] && echo "${C_GREEN}✓ 완료${C_RESET}" || echo "${C_RED}✗ 실패 $fail 건${C_RESET}"
}

action_reinstall_all() {
  require_uv || return 1
  local all=()
  while read -r p; do all+=("$p"); done < <(list_projects)
  if [[ ${#all[@]} -eq 0 ]]; then
    echo "${C_RED}하위에 pyproject.toml 을 가진 프로젝트가 없습니다.${C_RESET}"
    return 1
  fi

  echo
  echo "${C_BOLD}모두 재설치 대상 (${#all[@]}개):${C_RESET}"
  local map; map="$(build_index_map)"
  for p in "${all[@]}"; do
    local gidx; gidx="$(echo "$map" | awk -v k="$p" '$1==k{print $2}')"
    printf "  #%-2s %s\n" "$gidx" "$(project_name "$p")"
  done

  confirm "${C_YELLOW}모두 재설치할까요?${C_RESET}" || { echo "${C_DIM}취소됨.${C_RESET}"; return 0; }

  local ok=0 fail=0
  for p in "${all[@]}"; do
    do_reinstall_one "$p" && ok=$((ok+1)) || fail=$((fail+1))
  done
  echo
  echo "${C_BOLD}[요약]${C_RESET} 성공 $ok / 실패 $fail"
  [[ $fail -eq 0 ]] && echo "${C_GREEN}✓ 완료${C_RESET}" || echo "${C_RED}✗ 실패 $fail 건${C_RESET}"
}

action_install_new_only() {
  require_uv || return 1
  echo
  echo "${C_BOLD}[새로 추가된 프로젝트 설치]${C_RESET}"
  local fail=0 done_n=0 skip_n=0
  while read -r p; do
    local name; name="$(project_name "$p")"
    if is_installed "$name"; then
      skip_n=$((skip_n+1))
      continue
    fi
    do_install_one "$p" && done_n=$((done_n+1)) || fail=$((fail+1))
  done < <(list_projects)

  echo
  echo "${C_BOLD}[요약]${C_RESET} 설치 $done_n / 스킵(이미 설치) $skip_n / 실패 $fail"
  [[ $fail -eq 0 ]] && echo "${C_GREEN}✓ 완료${C_RESET}" || echo "${C_RED}✗ 실패 $fail 건${C_RESET}"
}

action_doctor() {
  require_uv || return 1
  echo
  echo "${C_BOLD}[doctor] 등록 스크립트 무결성 점검${C_RESET}"
  echo "${C_DIM}  $ uv tool list / command -v <cmd>${C_RESET}"

  if ! echo ":$PATH:" | grep -q ":$BIN_DIR:"; then
    echo "  ${C_RED}✗${C_RESET} PATH 에 $BIN_DIR 가 없습니다. (셸 설정에 추가 필요)"
  fi

  local issues=0 uninstalled=0 i=1
  while read -r p; do
    local name; name="$(project_name "$p")"
    if ! is_installed "$name"; then
      echo "  ${C_DIM}#$i · $p  (미설치, 정상)${C_RESET}"
      uninstalled=$((uninstalled+1))
      i=$((i+1))
      continue
    fi
    local scripts; scripts="$(project_scripts "$p")"
    if [[ -z "$scripts" ]]; then
      echo "  ${C_YELLOW}#$i ! $p  ([project.scripts] 항목 없음)${C_RESET}"
      i=$((i+1))
      continue
    fi
    while read -r cmd; do
      [[ -z "$cmd" ]] && continue
      if command -v "$cmd" >/dev/null 2>&1; then
        echo "  ${C_GREEN}#$i ✓${C_RESET} $p → $cmd  ($(command -v "$cmd"))"
      else
        echo "  ${C_RED}#$i ✗${C_RESET} $p → $cmd  (PATH 에서 찾을 수 없음)"
        issues=$((issues+1))
      fi
    done <<< "$scripts"
    i=$((i+1))
  done < <(list_projects)

  echo
  echo "${C_BOLD}[요약]${C_RESET} 미설치 $uninstalled / 문제 $issues"
  [[ $issues -eq 0 ]] && echo "${C_GREEN}✓ 문제 없음${C_RESET}" || echo "${C_RED}✗ 문제 $issues 건${C_RESET}"
}

action_list_detail() {
  echo
  echo "${C_BOLD}[목록 상세]${C_RESET}"
  local i=1
  while read -r p; do
    local name ver iv scripts path desc
    name="$(project_name "$p")"; ver="$(project_version "$p")"
    if is_installed "$name"; then iv="$(installed_version "$name")"; else iv="-"; fi
    scripts="$(project_scripts "$p" | paste -sd',' -)"
    path="$(project_path "$p")"
    desc="$(project_description "$p")"
    echo
    echo "  ${C_BOLD}#$i  ${name}${C_RESET}  (dir: $p)"
    [[ -n "$desc" ]] && echo "    desc     : $desc"
    echo "    version  : declared v$ver / installed ${iv}"
    echo "    scripts  : ${scripts:-—}"
    echo "    path     : $path"
    i=$((i+1))
  done < <(list_projects)
}

action_env() {
  echo
  echo "${C_BOLD}[환경 점검]${C_RESET}"
  echo "  uv       : $(have_uv && uv --version || echo 'not found')"
  echo "  python   : $(command -v python3 >/dev/null && python3 --version || echo 'not found')"
  echo "  BIN_DIR  : $BIN_DIR"
  if echo ":$PATH:" | grep -q ":$BIN_DIR:"; then
    echo "  PATH     : ${C_GREEN}ok${C_RESET}"
  else
    echo "  PATH     : ${C_RED}missing${C_RESET}  (Fish 셸 사용 시: fish_add_path ~/.local/bin)"
  fi
  have_uv && echo "  uv tool dir : $(uv tool dir 2>/dev/null || echo '?')"
}

# ------------------------------------------------------------
# 메인 루프
# ------------------------------------------------------------
main() {
  print_header
  while true; do
    print_menu
    read -r -p "> " choice || break
    case "$choice" in
      1) action_status ;;
      2) action_reinstall_all ;;
      3) action_bulk install ;;
      4) action_bulk reinstall ;;
      5) action_bulk uninstall ;;
      6) action_install_new_only ;;
      7) action_doctor ;;
      8) action_list_detail ;;
      9) action_env ;;
      0) action_help ;;
      99|q|Q|exit) echo "bye"; break ;;
      "") continue ;;
      *) echo "${C_RED}잘못된 선택: $choice${C_RESET}" ; continue ;;
    esac
    pause
  done
}

main "$@"