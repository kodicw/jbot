{
  pkgs,
  jbot-rotate-tasks-py,
  ...
}:
pkgs.runCommand "jbot-task-rotation-test"
  {
    nativeBuildInputs = [
      pkgs.python3
      pkgs.coreutils
    ];
  }
  ''
        TASKS_FILE="TASKS.md"
        ARCHIVE_FILE="TASKS.archive.md"
        
        cat > $TASKS_FILE <<EOF
    # JBot Task Board

    ## Strategic Vision
    Test task rotation.

    ## Active Tasks
    - [ ] Active task 1
    - [x] Completed task 1 (should be moved)
    - [ ] Active task 2

    ## Backlog
    - [x] Completed backlog task (should be moved)
    - [ ] Pending task

    ## Completed Tasks
    - [x] Old completed 1
    - [x] Old completed 2
    EOF

        python3 ${jbot-rotate-tasks-py} -t $TASKS_FILE -a $ARCHIVE_FILE -l 2

        # Verifications
        if grep -q "Completed task 1" $TASKS_FILE && ! grep -q "## Completed Tasks" $TASKS_FILE; then
           # Wait, if it's in Completed Tasks section it's okay.
           :
        fi

        # Check that [x] tasks are moved from Active/Backlog sections
        # We can't easily check sections with grep, but we can check if they are in the file
        
        # After rotation with limit 2:
        # Newly completed: Completed task 1, Completed backlog task
        # Old completed: Old completed 1, Old completed 2
        # Total completed: 4
        # Limit is 2, so 2 should be archived.
        
        if [ ! -f $ARCHIVE_FILE ]; then
          echo "Error: Archive file not created"
          exit 1
        fi

        ARCHIVE_COUNT=$(grep -c "\[x\]" $ARCHIVE_FILE)
        if [ "$ARCHIVE_COUNT" -ne 2 ]; then
          echo "Error: Expected 2 archived tasks, found $ARCHIVE_COUNT"
          exit 1
        fi

        TASKS_COUNT=$(grep -c "\[x\]" $TASKS_FILE)
        if [ "$TASKS_COUNT" -ne 2 ]; then
          echo "Error: Expected 2 tasks in TASKS.md, found $TASKS_COUNT"
          exit 1
        fi

        if grep -A 5 "## Active Tasks" $TASKS_FILE | grep -q "\[x\]"; then
          echo "Error: [x] task still in Active Tasks section"
          exit 1
        fi

        echo "Task rotation test passed!"
        touch $out
  ''
