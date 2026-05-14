# Reassembling the tar.gz

GitHub rejects single files > 100 MB. The full 230 MB
`kimi_multi_agent_swarm_5tasks.tar.gz` was split into 3 parts of
~90 MB each. To reassemble:

```bash
cat kimi_multi_agent_swarm_5tasks.tar.gz.part0* > kimi_multi_agent_swarm_5tasks.tar.gz
tar -tzf kimi_multi_agent_swarm_5tasks.tar.gz | head
```

The reassembled tar.gz contains the full bundle: 5x task.yaml +
5x gold.yaml + 5x single_run.json + 5x multi_run.json +
_upload_manifest.csv.

Verify with a SHA256 once committed:

```bash
sha256sum kimi_multi_agent_swarm_5tasks.tar.gz
```
