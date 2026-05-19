# AICL devkit

A tool for the student moderation competition. Send conversations incrementally to a moderation endpoint and track accuracy across malicious and benign data.

## How It Works

This tool reads conversation samples from `data/data.json` and sends them incrementally to a moderation API (default: `http://localhost:8080/moderate`). Each message is added to the conversation history before sending, so the moderator sees the full context at each step.

```
Turn 1: {assistant, user, assistant}          → moderation response
Turn 2: {assistant, user, assistant, user, assistant} → moderation response
Turn 3: {..., user}                           → moderation response
...
Final:  {..., report}                         → moderation response (full conversation)
```

If a response is `"malicious"`, that conversation stops early and moves to the next sample.

## Data Format

Each sample in `data/data.json` has a `label` (`"benign"` or `"malicious"`) and a `sample` with `messages` and an optional `report`:

```json
[{
  "label": "benign",
  "sample": {
    "messages": [
      {"role": "assistant", "content": "What would you like to report?"},
      {"role": "user", "content": "My bicycle was stolen."},
      ...
    ],
    "report": "On [Current Date], a theft was reported..."
  }
}]
```

## API Format

The moderation endpoint receives JSON with `messages` and an optional `report` field:

```json
{
  "messages": [
    {"role": "assistant", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "report": "Report summary..."  // optional, included only on the final request
}
```
