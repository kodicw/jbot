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
    echo '{"scope": "local", "status": "success", "summary": "Multi-agent test success"}' > "$MEMORY_OUTPUT"
  '';
in
pkgs.runCommand "jbot-multi-agent-unit-test"
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

    echo "Goal: Test multi-agent" > .project_goal
    echo "# Task Board" > TASKS.md
    mkdir -p .jbot/queues

    # Simulate another agent's memory
    echo '{"summary": "Task 1 completed"}' > .jbot/queues/lead.json

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
    if ! grep -q "\[lead\] Task 1 completed" .prompt_received; then
      echo "Error: Prompt did not contain other agent's memory"
      exit 1
    fi

    if [ ! -f .jbot/memory.log ]; then
      echo "Error: memory.log not created from queues"
      exit 1
    fi

    if [ -f .jbot/queues/lead.json ]; then
      echo "Error: lead.json not consolidated"
      exit 1
    fi

    touch $out
  ''
