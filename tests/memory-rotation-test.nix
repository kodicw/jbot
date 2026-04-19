{
  pkgs,
  jbot-rotate-py,
}:
pkgs.runCommand "memory-rotation-test"
  {
    buildInputs = [ pkgs.python3 ];
  }
  ''
    mkdir -p .jbot
    # Create a memory log with 150 entries
    for i in {1..150}; do
      echo "{\"agent\": \"test\", \"content\": {\"summary\": \"Memory $i\"}}" >> .jbot/memory.log
    done

    # Run rotation with limit 100
    python3 ${jbot-rotate-py} -l 100

    # Verify memory.log has 100 entries
    LOG_COUNT=$(wc -l < .jbot/memory.log)
    if [ "$LOG_COUNT" -ne 100 ]; then
      echo "Error: memory.log has $LOG_COUNT entries, expected 100"
      exit 1
    fi

    # Verify archive has 50 entries
    ARCHIVE_COUNT=$(wc -l < .jbot/memory.log.archive)
    if [ "$ARCHIVE_COUNT" -ne 50 ]; then
      echo "Error: memory.log.archive has $ARCHIVE_COUNT entries, expected 50"
      exit 1
    fi

    # Verify last entries are preserved
    if ! grep -q "Memory 150" .jbot/memory.log; then
      echo "Error: Latest memory entry not found in memory.log"
      exit 1
    fi

    # Verify first entries are archived
    if ! grep -q "Memory 1" .jbot/memory.log.archive; then
      echo "Error: First memory entry not found in archive"
      exit 1
    fi

    touch $out
  ''
