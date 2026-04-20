{
  pkgs,
  jbot-init-subproject-py,
  ...
}:
pkgs.runCommand "jbot-subproject-init-unit-test"
  {
    nativeBuildInputs = [
      pkgs.python3
      pkgs.coreutils
    ];
  }
  ''
    SUB_NAME="test-sub"
    SUB_GOAL="Verify that the sub-project initialization works correctly."
    
    python3 ${jbot-init-subproject-py} "$SUB_NAME" --goal "$SUB_GOAL"

    # Verifications
    if [ ! -d "$SUB_NAME" ]; then
      echo "Error: Sub-project directory not created"
      exit 1
    fi

    if [ ! -d "$SUB_NAME/.jbot/directives" ]; then
      echo "Error: Directives directory not created"
      exit 1
    fi

    if [ ! -f "$SUB_NAME/TASKS.md" ]; then
      echo "Error: TASKS.md not created"
      exit 1
    fi

    if ! grep -q "$SUB_GOAL" "$SUB_NAME/TASKS.md"; then
      echo "Error: TASKS.md does not contain the specified goal"
      exit 1
    fi

    if [ ! -f "$SUB_NAME/.project_goal" ]; then
      echo "Error: .project_goal not created"
      exit 1
    fi

    if ! grep -q "$SUB_GOAL" "$SUB_NAME/.project_goal"; then
      echo "Error: .project_goal content incorrect"
      exit 1
    fi

    if [ ! -f "$SUB_NAME/BILLING.md" ]; then
      echo "Error: BILLING.md not created"
      exit 1
    fi

    if [ ! -f "$SUB_NAME/CHANGELOG.md" ]; then
      echo "Error: CHANGELOG.md not created"
      exit 1
    fi

    echo "Sub-project initialization test passed!"
    touch $out
  ''
