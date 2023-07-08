#!/usr/bin/env bash

set -euo pipefail

export FORMAT_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "${FORMAT_SCRIPT_DIR}/util.sh"

if ! hash poetry ; then
  die \
    "Please install python poetry in order to run formatting, and manage the project." \
    "You can learn how to install it at: <https://python-poetry.org>"
fi

cd "${FORMAT_SCRIPT_DIR}/../../"
(>&2 echo "Running Poetry Install to ensure dependency for formatting exists.")
output_on_error poetry install
(>&2 echo "Done.")
poetry run black --verbose -t py37 source/