{
  pkgs,
  jbot-purge-py,
  ...
}:
pkgs.runCommand "jbot-directive-purge-test"
  {
    nativeBuildInputs = [
      pkgs.python3
      pkgs.coreutils
    ];
  }
  ''
    export PROJECT_DIR=$TMPDIR/project
    mkdir -p $PROJECT_DIR
    cd $PROJECT_DIR

    mkdir -p .jbot/directives
    
    # 1. Active directive (no date)
    echo "Active directive content" > .jbot/directives/001_active.txt
    
    # 2. Expired directive (filename date in the past)
    echo "Expired filename directive content" > .jbot/directives/002_2020-01-01_expired.md
    
    # 3. Future directive (filename date in the future)
    echo "Future filename directive content" > .jbot/directives/003_2099-01-01_future.md
    
    # 4. Expired directive (content expiration in the past)
    cat <<EOF > .jbot/directives/004_expired_content.md
# Directive 004
Expiration: 2020-01-01
Expired content directive content
EOF

    # 5. Future directive (content expiration in the future)
    cat <<EOF > .jbot/directives/005_future_content.md
# Directive 005
Expiration: 2099-01-01
Future content directive content
EOF

    # Run purge script
    python3 ${jbot-purge-py}

    # Verifications
    echo "Verifying purged directives..."
    
    if [ ! -f .jbot/directives/001_active.txt ]; then
      echo "Error: Active directive was purged"
      exit 1
    fi

    if [ -f .jbot/directives/002_2020-01-01_expired.md ]; then
      echo "Error: Expired filename directive was NOT purged"
      exit 1
    fi

    if [ ! -f .jbot/directives/archive/002_2020-01-01_expired.md ]; then
      echo "Error: Expired filename directive was not found in archive"
      exit 1
    fi

    if [ ! -f .jbot/directives/003_2099-01-01_future.md ]; then
      echo "Error: Future filename directive was purged"
      exit 1
    fi

    if [ -f .jbot/directives/004_expired_content.md ]; then
      echo "Error: Expired content directive was NOT purged"
      exit 1
    fi

    if [ ! -f .jbot/directives/archive/004_expired_content.md ]; then
      echo "Error: Expired content directive was not found in archive"
      exit 1
    fi

    if [ ! -f .jbot/directives/005_future_content.md ]; then
      echo "Error: Future content directive was purged"
      exit 1
    fi

    echo "All directive purge checks passed!"
    touch $out
  ''
