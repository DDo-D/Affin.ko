#!/bin/zsh
# Affin.ko core — en-US.lproj → sed dictionary → ko.lproj (UTF-16LE, CRLF)
# Source from other scripts: source "${REPO_ROOT}/affin-ko-lib.zsh"

typeset -g AFFIN_KO_TARGET_VERSION="3.2.1"
typeset -g AFFIN_KO_TARGET_BUILD="4425"

affin_ko_repo_root() {
  local script="${1:-${(%):-%x}}"
  cd "${script:A:h}" && pwd
}

affin_ko_detect_app() {
  local app="${1:-${AFFINITY_APP:-/Applications/Affinity.app}}"
  if [[ ! -d "${app}/Contents/Resources/en-US.lproj" ]]; then
    print -u2 "Affinity.app not found or unsupported layout: ${app}"
    return 1
  fi
  print -r -- "${app}"
}

affin_ko_app_version() {
  local app="$1"
  local key="$2"
  /usr/libexec/PlistBuddy -c "Print ${key}" "${app}/Contents/Info.plist" 2>/dev/null
}

affin_ko_version_check() {
  local app="$1"
  local short build
  short="$(affin_ko_app_version "${app}" CFBundleShortVersionString)"
  build="$(affin_ko_app_version "${app}" CFBundleVersion)"
  if [[ "${short}" != "${AFFIN_KO_TARGET_VERSION}" || "${build}" != "${AFFIN_KO_TARGET_BUILD}" ]]; then
    print -u2 "Warning: installed Affinity ${short} (${build}) ≠ tested ${AFFIN_KO_TARGET_VERSION} (${AFFIN_KO_TARGET_BUILD})."
    print -u2 "Patch may still work; report issues with your exact version."
    return 1
  fi
  return 0
}

# Normalize line endings to CRLF (matches official ja/en-US .strings)
affin_ko_to_crlf() {
  local src="$1" dst="$2"
  perl -pe 's/\r?\n/\r\n/g' "${src}" >"${dst}"
}

affin_ko_process_pair() {
  local en_dir="$1"
  local ko_dir="$2"
  local dictionary="$3"
  local file count i name tmp_utf8 tmp_sed tmp_crlf

  [[ -d "${en_dir}" ]] || { print -u2 "Missing: ${en_dir}"; return 1 }
  mkdir -p "${ko_dir}"

  # Only *.strings (same as legacy Affinity-ko)
  local -a files
  files=("${en_dir}"/*.strings(N))
  count=${#files[@]}
  if (( count == 0 )); then
    print -u2 "No .strings in ${en_dir}"
    return 1
  fi

  for (( i = 1; i <= count; i++ )); do
    name="${files[i]:t}"
    print -f "→ ${i}/${count}\t${name}\n"
    tmp_utf8="$(mktemp "${TMPDIR:-/tmp}/affin-ko.utf8.XXXXXX")"
    tmp_sed="$(mktemp "${TMPDIR:-/tmp}/affin-ko.sed.XXXXXX")"
    tmp_crlf="$(mktemp "${TMPDIR:-/tmp}/affin-ko.crlf.XXXXXX")"
    iconv -f UTF-16LE -t UTF-8 "${files[i]}" >"${tmp_utf8}" || {
      print -u2 "iconv read failed: ${files[i]}"
      rm -f "${tmp_utf8}" "${tmp_sed}" "${tmp_crlf}"
      return 1
    }
    sed -f "${dictionary}" "${tmp_utf8}" >"${tmp_sed}"
    affin_ko_to_crlf "${tmp_sed}" "${tmp_crlf}"
    iconv -f UTF-8 -t UTF-16LE "${tmp_crlf}" >"${ko_dir}/${name}"
    rm -f "${tmp_utf8}" "${tmp_sed}" "${tmp_crlf}"
  done
}

affin_ko_build_from_app() {
  local app="$1"
  local out_root="$2"
  local dictionary="$3"
  local short build stamp manifest

  app="$(affin_ko_detect_app "${app}")" || return 1
  short="$(affin_ko_app_version "${app}" CFBundleShortVersionString)"
  build="$(affin_ko_app_version "${app}" CFBundleVersion)"
  stamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  mkdir -p "${out_root}/Resources/ko.lproj"
  mkdir -p "${out_root}/Frameworks/libcocoaui.framework/Versions/A/Resources/ko.lproj"

  print "→ Building Resources/ko.lproj"
  affin_ko_process_pair \
    "${app}/Contents/Resources/en-US.lproj" \
    "${out_root}/Resources/ko.lproj" \
    "${dictionary}" || return 1

  print "→ Building Frameworks/.../ko.lproj"
  affin_ko_process_pair \
    "${app}/Contents/Frameworks/libcocoaui.framework/Versions/A/Resources/en-US.lproj" \
    "${out_root}/Frameworks/libcocoaui.framework/Versions/A/Resources/ko.lproj" \
    "${dictionary}" || return 1

  manifest="${out_root}/manifest.json"
  cat >"${manifest}" <<EOF
{
  "name": "affin.ko",
  "affinity_short_version": "${short}",
  "affinity_build": "${build}",
  "target_short_version": "${AFFIN_KO_TARGET_VERSION}",
  "target_build": "${AFFIN_KO_TARGET_BUILD}",
  "built_at": "${stamp}",
  "encoding": "UTF-16LE",
  "line_endings": "CRLF",
  "paths": [
    "Resources/ko.lproj",
    "Frameworks/libcocoaui.framework/Versions/A/Resources/ko.lproj"
  ]
}
EOF
  print "→ Wrote ${manifest}"
}

affin_ko_install_to_app() {
  local bundle_root="$1"
  local app="$2"

  app="$(affin_ko_detect_app "${app}")" || return 1

  mkdir -p "${app}/Contents/Resources/ko.lproj"
  mkdir -p "${app}/Contents/Frameworks/libcocoaui.framework/Versions/A/Resources/ko.lproj"

  print "→ Installing Resources/ko.lproj"
  cp -f "${bundle_root}/Resources/ko.lproj/"*.strings \
    "${app}/Contents/Resources/ko.lproj/" 2>/dev/null || {
    print -u2 "Missing bundle: ${bundle_root}/Resources/ko.lproj"
    return 1
  }

  print "→ Installing Frameworks/.../ko.lproj"
  cp -f "${bundle_root}/Frameworks/libcocoaui.framework/Versions/A/Resources/ko.lproj/"*.strings \
    "${app}/Contents/Frameworks/libcocoaui.framework/Versions/A/Resources/ko.lproj/" 2>/dev/null || {
    print -u2 "Missing bundle: ${bundle_root}/Frameworks/.../ko.lproj"
    return 1
  }
}
