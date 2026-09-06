#!/usr/bin/env bash
# Build both decks from deck.json, validate, and rasterize for visual QA.
set -euo pipefail
DECK_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL=/root/.claude/skills/synced/518cb4f8-68dc-4415-8bb7-be53715a24c9_9efd9eaf-9f84-49dc-8aae-642c80990b3d/pptx/scripts
QA=/tmp/deckqa
JSON="${1:-$DECK_DIR/deck.json}"

cd "$DECK_DIR"
node render.js "$JSON" "Presentation.pptx"
node render.js "$JSON" "Presentation_with_Arabic_notes.pptx" --notes
python3 "$SKILL/office/validate.py" Presentation.pptx | tail -3
python3 "$SKILL/office/validate.py" Presentation_with_Arabic_notes.pptx | tail -3

mkdir -p "$QA"
cp Presentation_with_Arabic_notes.pptx "$QA/deck.pptx"
cd "$QA"
python3 "$SKILL/office/soffice.py" --headless --convert-to pdf deck.pptx >/dev/null 2>&1 || echo "soffice conversion failed"
if [ -f deck.pdf ]; then
  rm -f slide-*.jpg
  pdftoppm -jpeg -r 90 deck.pdf slide
  ls -1 "$QA"/slide-*.jpg | wc -l
fi
