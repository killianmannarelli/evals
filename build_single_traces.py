"""Wrap each work_single/<inst>/solution_summary.md into a synthetic
3-span OpenInference OTel JSON per the pipeline spec (Stage 6 Path B step 3)."""
import json, os, secrets, datetime, yaml, glob

WORK = '/home/user/evals/work_single'

INSTANCES = sorted(d for d in os.listdir(WORK) if os.path.isdir(os.path.join(WORK, d)))

def hex_id(n=16):
    return '0x' + secrets.token_hex(n // 2)

def ts(offset_s, base):
    return (base + datetime.timedelta(seconds=offset_s)).isoformat().replace('+00:00', 'Z')

for inst in INSTANCES:
    work_dir = os.path.join(WORK, inst)
    task_yaml = os.path.join(work_dir, 'task.yaml')
    sum_md = os.path.join(work_dir, 'solution_summary.md')
    with open(task_yaml) as f:
        td = yaml.safe_load(f)
    task_id = td['task_id']
    user_prompt = td['prompt']
    system_prompt = (
        "You are a single-agent solver running outside the multi-agent "
        "swarm. Solve the supplied task end-to-end yourself; do not spawn "
        "sub-agents."
    )

    if os.path.exists(sum_md):
        with open(sum_md) as f:
            assistant_content = f.read()
        status = 'OK'
    else:
        partial_files = []
        for ext in ('md', 'json', 'txt', 'tsv', 'py', 'html'):
            partial_files += glob.glob(os.path.join(work_dir, 'app', 'artifact', f'*.{ext}'))
            partial_files += glob.glob(os.path.join(work_dir, f'*.{ext}'))
        partial_files = sorted({p.replace(WORK + '/', '') for p in partial_files})
        assistant_content = (
            "# Partial completion\n\n"
            "Two consecutive runs of this single-agent solver terminated "
            "with infrastructure errors before solution_summary.md could "
            "be written:\n"
            "  - run 1: \"API Error: 400 Could not process image\"\n"
            "  - run 2: \"API Error: The socket connection was closed "
            "unexpectedly\"\n\n"
            "Files actually produced in the workspace before the second "
            "failure:\n"
            + "\n".join(f"- {p}" for p in partial_files)
            + "\n"
        )
        status = 'ERROR'

    trace_id = secrets.token_hex(16)
    agent_span_id = hex_id()
    gen_span_id = hex_id()
    tool_span_id = hex_id()
    base = datetime.datetime.now(datetime.timezone.utc)
    t0, t1, t2, t3 = ts(0, base), ts(0.1, base), ts(1.0, base), ts(1.1, base)
    spans = [
        {
            'name': 'Agent workflow',
            'context': {'trace_id': '0x' + trace_id, 'span_id': agent_span_id, 'trace_state': '[]'},
            'kind': 'SpanKind.INTERNAL',
            'parent_id': None,
            'start_time': t0, 'end_time': t3,
            'status': {'status_code': status},
            'attributes': {
                'openinference.span.kind': 'AGENT',
                'agent.name': 'single_solver',
                'agent.task_id': task_id,
                'agent.mode': 'single',
                'agent.runner': 'claude-code-agent-subagent',
            },
            'events': [], 'links': [],
            'resource': {'attributes': {'service.name': 'single-agent-solver'}, 'schema_url': ''},
        },
        {
            'name': 'generation',
            'context': {'trace_id': '0x' + trace_id, 'span_id': gen_span_id, 'trace_state': '[]'},
            'kind': 'SpanKind.INTERNAL',
            'parent_id': agent_span_id,
            'start_time': t1, 'end_time': t2,
            'status': {'status_code': status},
            'attributes': {
                'openinference.span.kind': 'LLM',
                'llm.system': 'anthropic',
                'llm.model_name': 'claude-opus-4-7',
                'llm.input_messages.0.message.role': 'system',
                'llm.input_messages.0.message.content': system_prompt,
                'llm.input_messages.1.message.role': 'user',
                'llm.input_messages.1.message.content': user_prompt,
                'llm.output_messages.0.message.role': 'assistant',
                'llm.output_messages.0.message.content': assistant_content,
            },
            'events': [], 'links': [],
            'resource': {'attributes': {'service.name': 'single-agent-solver'}, 'schema_url': ''},
        },
        {
            'name': 'write_file',
            'context': {'trace_id': '0x' + trace_id, 'span_id': tool_span_id, 'trace_state': '[]'},
            'kind': 'SpanKind.INTERNAL',
            'parent_id': agent_span_id,
            'start_time': t2, 'end_time': t3,
            'status': {'status_code': status},
            'attributes': {
                'openinference.span.kind': 'TOOL',
                'tool.name': 'write_file',
                'tool.parameters': json.dumps({'path': 'solution_summary.md', 'content_length': len(assistant_content)}),
                'tool.output': (
                    f'wrote solution_summary.md ({len(assistant_content)} bytes)'
                    if status == 'OK' else 'partial — no solution_summary.md written'
                ),
            },
            'events': [], 'links': [],
            'resource': {'attributes': {'service.name': 'single-agent-solver'}, 'schema_url': ''},
        },
    ]

    out = os.path.join(work_dir, f'{inst}_single_run.json')
    with open(out, 'w') as f:
        json.dump(spans, f, indent=2)
    print(f'wrote {out}  ({os.path.getsize(out)} B, status={status})')

print(f'\n{len(INSTANCES)} traces emitted')
