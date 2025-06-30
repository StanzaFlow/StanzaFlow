# Workflow: Ticket Triage

## Agent: Bot
- Step: Hello
  artifact: hello.txt
  timeout: 30

- Step: Analyze ticket
  artifact: analysis.json
  retry: 3
  on_error: escalate

## Agent: Human
- Step: Review analysis
  artifact: review.md
  finally: cleanup 