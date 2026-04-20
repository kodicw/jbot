{
  pkgs,
  jbot-agent-py,
  jbot-dashboard-py,
  jbot-prompt-txt,
  ...
}:
let
  mockGemini = pkgs.writeShellScriptBin "gemini" ''
    # Store the prompt passed via -p
    while [[ $# -gt 0 ]]; do
      case "$1" in
        -p)
          echo "$2" > "$PROJECT_DIR/.prompt_received"
          shift 2
          ;;
        *)
          shift
          ;;
      esac
    done
    echo '{"scope": "local", "status": "success", "summary": "Directive expiration test success"}' > "$MEMORY_OUTPUT"
  '';
in
pkgs.runCommand "jbot-directive-expiration-test"
  {
    nativeBuildInputs = [
      pkgs.python3
      pkgs.coreutils
      pkgs.findutils
      pkgs.jq
      mockGemini
    ];
  }
  ''
        export PROJECT_DIR=$TMPDIR/project
        mkdir -p $PROJECT_DIR
        cd $PROJECT_DIR

        # Initial files
        cp ${jbot-dashboard-py} jbot-dashboard.py
        echo "Goal: Test directive expiration" > .project_goal
        echo "# Task Board" > TASKS.md
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

        mkdir -p .jbot
        echo '{"dev": {"role": "Lead", "description": "Lead Dev", "projectDir": "'$PROJECT_DIR'"}}' > .jbot/agents.json

        export AGENT_NAME="dev"
        export AGENT_ROLE="Lead"
        export AGENT_DESCRIPTION="Lead Dev"
        export PROMPT_FILE="${jbot-prompt-txt}"
        export GEMINI_PACKAGE="gemini"
        export MEMORY_OUTPUT=".jbot/queues/dev.json"

        # Use a fixed date for the test if possible? 
        # The python script uses datetime.now().strftime("%Y-%m-%d")
        # We can't easily mock datetime.now() in python from the outside without a wrapper or patching.
        # But since 2020-01-01 is definitely in the past and 2099-01-01 is definitely in the future,
        # it should work regardless of when the test is run (unless it's after 2099).

        python3 ${jbot-agent-py}

        # Verifications
        echo "Verifying prompt content..."
        
        if ! grep -q "Active directive content" .prompt_received; then
          echo "Error: Active directive not found in prompt"
          exit 1
        fi

        if grep -q "Expired filename directive content" .prompt_received; then
          echo "Error: Expired filename directive FOUND in prompt"
          exit 1
        fi

        if ! grep -q "Future filename directive content" .prompt_received; then
          echo "Error: Future filename directive not found in prompt"
          exit 1
        fi

        if grep -q "Expired content directive content" .prompt_received; then
          echo "Error: Expired content directive FOUND in prompt"
          exit 1
        fi

        if ! grep -q "Future content directive content" .prompt_received; then
          echo "Error: Future content directive not found in prompt"
          exit 1
        fi

        echo "All directive expiration checks passed!"
        touch $out
  ''
