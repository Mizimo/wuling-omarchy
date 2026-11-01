#!/bin/bash
# Disposable route experiment. Failure to read lock state leaves it closed.
set -euo pipefail
[[ $(omarchy-shell lock isLocked) == false ]] || exit 0
exec omarchy-shell shell toggle research.focus
