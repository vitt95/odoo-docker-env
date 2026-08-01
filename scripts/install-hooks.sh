#!/usr/bin/env bash
# =============================================================================
# install-hooks.sh — point git at the versioned hooks in scripts/hooks.
#
# `core.hooksPath` rather than copying into .git/hooks: a hook that lives in the
# repository is reviewable, and a change to it arrives with the pull request that
# needs it.
#
#   ./scripts/install-hooks.sh
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

chmod +x scripts/hooks/*
git config core.hooksPath scripts/hooks

printf 'Hooks enabled from scripts/hooks (core.hooksPath).\n'
printf '  pre-push: runs the four boundary checks of D24.\n'
