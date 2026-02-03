# Specs Updates Generator

A CLI tool to automatically process Slack discussions and generate specification updates using AI classification.

## Features

- **Slack Integration**: Fetch and normalize Slack threads
- **AI Classification**: Automatically classify discussions as Open Questions (OQ) or Proposed Updates (PU)
- **State Management**: Track progress through a defined workflow
- **Traceability**: Full audit trail of all processed data

## Setup

1. **Install dependencies**:
   ```bash
   pip install slack-sdk openai python-dotenv
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Initialize sync point**:
   ```bash
   python agent.py init_sync
   ```

## Usage

### Available Commands

- `python agent.py ingest` - Fetch and classify new Slack threads
- `python agent.py art_list` - List all artifacts
- `python agent.py oq_list` - List all open questions
- `python agent.py pu_list` - List all proposed updates
- `python agent.py artifact_transform` - Transform artifacts to OQ/PU
- `python agent.py oq_transform <oq_id>` - Convert OQ to PU with decision
- `python agent.py approve_pu <pu_id>` - Approve a proposed update
- `python agent.py change_status <artifact_id> <status>` - Manually change artifact status

## Workflow

1. **Ingest**: Fetch Slack threads → Create Artifacts
2. **Transform**: Artifacts → Open Questions or Proposed Updates
3. **Decide**: Open Questions + Decisions → Proposed Updates
4. **Approve**: Proposed Updates → Spec Updates

## Data Storage

All data is stored in `data/` directory:
- `artifacts.json` - Classified discussions
- `open_questions.json` - Questions requiring decisions
- `proposed_updates.json` - Updates pending approval
- `specs_updates.json` - Approved specification changes
- `slack_threads.json` - Raw Slack data (traceability)
- `conversations.json` - Normalized conversations (traceability)

## License

MIT
