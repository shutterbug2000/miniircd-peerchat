#!/usr/bin/env bash

output_on_error() {
  save=$-
  # Error mode prevents us from displaying as soon as the command fails.
  #
  # Disable it temporarily.
  error_mode_was_on=0
  if [[ $save =~ e ]]; then
    error_mode_was_on=1
    set +e
  fi

  local rc=
  local stdouterr=
  stdouterr="$(mktemp -u)"

  mkfifo "$stdouterr"
  exec 3<>"$stdouterr"
  rm "$stdouterr"

  ( "$@" 1>&3 2>&3 )

  rc=$?

  if [ $rc -ne 0 ]; then
    cat <&3 &
    sleep 0.5s
    exec 3>&-
  fi

  if [ $error_mode_was_on -eq 1 ]; then
    set -e
  fi

  return $rc
}
export -f output_on_error

die() {
  echo "ERROR: $1" >&2
  shift
  while [[ -n ${1-} ]]; do
    echo "    $1" >&2
    shift
  done
  exit 1
}
export -f die