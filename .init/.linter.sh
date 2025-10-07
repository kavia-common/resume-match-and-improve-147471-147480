#!/bin/bash
cd /home/kavia/workspace/code-generation/resume-match-and-improve-147471-147480/resume_job_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

