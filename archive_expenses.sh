#!/bin/bash
# archive_expenses.sh — archive expense files into ./archives and log actions

ARCHIVE_DIR="archives"
LOG_FILE="archive_log.txt"
PATTERN="expenses_*.txt"

if [ ! -d "$ARCHIVE_DIR" ]; then
  mkdir -p "$ARCHIVE_DIR"
fi

# If a single date is passed, print that archived file (if present).
if [ $# -eq 1 ]; then
  DATE="$1"
  FNAME="expenses_${DATE}.txt"
  FOUND=$(find "$ARCHIVE_DIR" -type f -name "${FNAME}" | head -n 1)
  if [ -n "$FOUND" ]; then
    echo "Found archived file: $FOUND"
    echo "---- CONTENT ----"
    cat "$FOUND"
    exit 0
  else
    echo "No archived file for date ${DATE} in ${ARCHIVE_DIR}."
    exit 1
  fi
fi

shopt -s nullglob
files=( $PATTERN )
if [ ${#files[@]} -eq 0 ]; then
  echo "No expense files to archive."
  exit 0
fi

for f in "${files[@]}"; do
  ts=$(date +"%Y%m%d-%H%M%S")
  base="${f%.txt}"
  newname="${base}-${ts}.txt"

  mv "$f" "$ARCHIVE_DIR/$newname"

  {
    echo "---- ARCHIVE ENTRY ----"
    echo "Timestamp: $(date --iso-8601=seconds)"
    echo "Original File: $f"
    echo "Archived As: $ARCHIVE_DIR/$newname"
    echo "Content:"
    cat "$ARCHIVE_DIR/$newname"
    echo
  } >> "$LOG_FILE"

  echo "Archived $f as $ARCHIVE_DIR/$newname"
done