#!/usr/bin/env bash

set -euo pipefail

export LINT_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "${LINT_SCRIPT_DIR}/../local/util.sh"

if ! hash poetry ; then
  die \
    "Please install python poetry in order to run linting, and manage the project." \
    "You can learn how to install it at: <https://python-poetry.org>"
fi

cd "${LINT_SCRIPT_DIR}/../../"
(>&2 echo "Running Poetry Install to ensure dependency for linting exists.")
output_on_error poetry install
(>&2 echo "Done.")
poetry run black --verbose --check -t py37 ./source/
poetry run pyright --level warning --pythonversion 3.7 --warnings ./source/
poetry run ruff check ./source/