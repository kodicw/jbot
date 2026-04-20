{
  pkgs,
  jbot-scripts,
  jbot_prompt_txt,
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
    echo '{"scope": "local", "status": "success", "summary": "Handover test success"}' > "$MEMORY_OUTPUT"
  '';
in
pkgs.runCommand "jbot-handover-unit-test"
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

    echo "Goal: Test handover" > .project_goal

    # Setup a stateful task simulation
    cat <<EOF > TASKS.md
    # JBot Task Board
    ## Active Tasks
    - [ ] Implement new feature (Agent: lead) - Status: Done
    - [ ] Verify new feature (Agent: tester) - Status: To Do
    EOF

    mkdir -p .jbot
    echo '{"tester": {"role": "QA", "description": "QA Tester", "projectDir": "'$PROJECT_DIR'"}, "lead": {"role": "Lead", "description": "Lead Dev", "projectDir": "'$PROJECT_DIR'"}}' > .jbot/agents.json

    export AGENT_NAME="tester"
    export AGENT_ROLE="QA"
    export AGENT_DESCRIPTION="QA Tester"
    export PROMPT_FILE="${jbot_prompt_txt}"
    export GEMINI_PACKAGE="gemini"
    export MEMORY_OUTPUT=".jbot/queues/tester.json"

    python3 ${jbot-scripts}/jbot-agent.py

    # Verifications
    if ! grep -q "Implement new feature (Agent: lead) - Status: Done" .prompt_received; then
      echo "Error: Prompt did not contain completed task for handover"
      exit 1
    fi

    if ! grep -q "Verify new feature (Agent: tester) - Status: To Do" .prompt_received; then
      echo "Error: Prompt did not contain pending task for handover"
      exit 1
    fi

    echo "Handover verification successful."
    touch $out
  ''
