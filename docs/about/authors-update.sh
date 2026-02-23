#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# Keep authors in the order of appearance and use awk to filter out dupes
git log --format='- %aN <%aE>' --reverse | awk '!x[$0]++' > AUTHORS
