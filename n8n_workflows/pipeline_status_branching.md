# Pipeline Status Branching

Use the pipeline response `status` field to decide what n8n should do next.

## Branching rules

```text
status = success -> normal end
status = partial_success -> notify human reviewer
status = failed -> send alert
```

## Response fields n8n should read

- `status`
- `message`
- `data.pipeline_report`
- `data.collect_result`
- `data.ingestion_result`
- `data.promotion_result`
- `errors`

## Suggested branching logic

```text
HTTP Request: POST /pipeline/run
↓
IF Node: status == success
├─ true  -> success path
└─ false -> IF Node: status == partial_success
             ├─ true  -> partial_success path
             └─ false -> failed path
```

If your n8n version or team preference favors a Switch node, it can use the same `status` field and branch to three paths.

## What each branch means

### success

The pipeline completed normally. You can end the workflow or continue to downstream automation.

### partial_success

The pipeline completed with warnings or recoverable issues. Notify a human reviewer and inspect:

- `data.pipeline_report`
- `data.collect_result`
- `data.ingestion_result`
- `data.promotion_result`

### failed

The pipeline did not complete successfully. Check:

1. API token
2. Supabase key
3. output path
4. batch report
5. pipeline report
