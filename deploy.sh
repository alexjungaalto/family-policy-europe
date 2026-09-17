#!/bin/zsh
# Publish to GitHub Pages: https://alexjungaalto.github.io/family-policy-europe/
# The whole site is docs/ (index.html + data/europe.geojson + data/policies.json),
# a static Leaflet app served from the `docs/` folder of the main branch.
#
#   ./deploy.sh            # link-check, stamp data version, commit, push
#   SKIP_LINK_CHECK=1 ./deploy.sh
set -e
cd "$HOME/playground/FamilyPolicyEurope"

if [[ "${SKIP_LINK_CHECK:-0}" == "1" ]]; then
  echo "link check SKIPPED (SKIP_LINK_CHECK=1)"
else
  echo "checking links..."
  if ! python3 check_links.py; then
    echo "ABORT: dead link(s) found — not deploying. Fix them or run with SKIP_LINK_CHECK=1." >&2
    exit 1
  fi
fi

STAMP=$(date +%Y%m%d%H%M%S)
sed -i '' "s/const DATA_V='[^']*'/const DATA_V='${STAMP}'/" docs/index.html
echo "data version stamped: ${STAMP}"

git add -A
git commit -m "Deploy ${STAMP}

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" || echo "nothing to commit"
git push origin main
echo "pushed — GitHub Pages rebuilds in ~1 min"
sleep 60
CODE=$(curl -sS -o /dev/null -w "%{http_code}" "https://alexjungaalto.github.io/family-policy-europe/")
echo "DEPLOY COMPLETE: page=HTTP${CODE}"
echo "Live at: https://alexjungaalto.github.io/family-policy-europe/"
