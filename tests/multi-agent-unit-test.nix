{
  pkgs,
  jbot-agent-py,
  jbot-prompt-txt,
  ...
}:
let
  mockGemini = pkgs.writeShellScriptBin "gemini" ''
    # Store the prompt for verification
    echo "$AGENT_NAME" > "$PROJECT_DIR/.called_$AGENT_NAME"
    echo '{"scope": "local", "status": "success", "summary": "Finished work", "next_step": "None"}' > "$MEMORY_OUTPUT"
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
} ''
  export PROJECT_DIR=$TMPDIR/project
  mkdir -p $PROJECT_DIR
  cd $PROJECT_DIR

  # Initial files
  echo "Goal: Test multi-agent coordination" > .project_goal
  echo "# Task Board" > TASKS.md
  mkdir -p .jbot
  echo '{"agent1": {"role": "Dev", "projectDir": "'$PROJECT_DIR'"}, "agent2": {"role": "QA", "projectDir": "'$PROJECT_DIR'"}}' > .jbot/agents.json

  export PROMPT_FILE="${jbot-prompt-txt}"
  export GEMINI_PACKAGE="gemini"

  # 1. Run agent1
  export AGENT_NAME="agent1"
  export AGENT_ROLE="Dev"
  export AGENT_DESCRIPTION="Developer"
  export MEMORY_OUTPUT=".jbot/queues/agent1.json"
  python3 ${jbot-agent-py}

  if [ ! -f .jbot/queues/agent1.json ]; then
    echo "Error: agent1 memory not created"
    exit 1
  fi

  # 2. Run agent2 - it should consolidate agent1's memory
  export AGENT_NAME="agent2"
  export AGENT_ROLE="QA"
  export AGENT_DESCRIPTION="Tester"
  export MEMORY_OUTPUT=".jbot/queues/agent2.json"
  python3 ${jbot-agent-py}

  if [ -f .jbot/queues/agent1.json ]; then
    echo "Error: agent1 memory was not consolidated by agent2"
    exit 1
  fi

  if [ ! -f .jbot/memory.log ]; then
    echo "Error: memory.log not created"
    exit 1
  fi

  if ! grep -q "agent1" .jbot/memory.log; then
    echo "Error: agent1 not found in memory.log"
    exit 1
  fi

  touch $out
''
