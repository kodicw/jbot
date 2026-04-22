{
  pkgs,
  jbot-cli-py,
  ...
}:
pkgs.runCommand "jbot-memory-rotation-test"
  {
    nativeBuildInputs = [
      pkgs.python3
      pkgs.coreutils
      pkgs.jq
    ];
  }
  ''
    export PROJECT_DIR=$TMPDIR/project
    mkdir -p $PROJECT_DIR
    cd $PROJECT_DIR

    # Need .project_goal to identify project root
    echo "Goal" > .project_goal

    mkdir -p .jbot
    # Create a memory log with 20 entries
    for i in {1..20}; do
      echo '{"agent": "test", "content": {"summary": "entry '$i'"}, "timestamp": "2026-04-20T12:00:00"}' >> .jbot/memory.log
    done

    # Run rotation via CLI with limit 10
    export PYTHONPATH=$PYTHONPATH:${dirOf jbot-cli-py}
    python3 ${jbot-cli-py} rotate memory --limit 10

    # Verifications
    echo "Verifying memory rotation..."

    if [ ! -f .jbot/memory.log.archive ]; then
      echo "Error: Archive file not created"
      exit 1
    fi

    LOG_LINES=$(wc -l < .jbot/memory.log)
    if [ "$LOG_LINES" -ne 10 ]; then
      echo "Error: Memory log should have 10 lines, but has $LOG_LINES"
      exit 1
    fi

    ARCHIVE_LINES=$(wc -l < .jbot/memory.log.archive)
    if [ "$ARCHIVE_LINES" -ne 10 ]; then
      echo "Error: Archive should have 10 lines, but has $ARCHIVE_LINES"
      exit 1
    fi

    echo "Memory rotation checks passed!"
    touch $out
  ''
