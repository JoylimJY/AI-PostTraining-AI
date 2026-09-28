# Forked run (from an archived trajectory, at a chosen node)

- Run: claude_opus46_gsm8k_qwen3_1_7b_20260902_005050_fork_run2_20260925_005947
- Archive: /home/user/ptb/opus46/trajectories_opus46/autonomous_gsm8k_886c6165
- Source run: claude_opus46_gsm8k_qwen3_1_7b_20260902_005050 (budget 10 h, agent claude-opus-4-6)
- Fork node: Run 2 (step_002_sft_rawtext: raw-text SFT, 42% on 50 samples) and its checkpoint (about 2h51m into the source run)
- Fork state: trajectory.jsonl lines 1..(result of the tool call on line 1234); see fork_source/fork_manifest.json
- Forked at: 2026-09-25T00:59:49+0800
- Fresh time budget: 7 hours
- Hint given to the agent: Please evaluate whether the current strategy needs adjustment.
- Benchmark: gsm8k
- Agent: Claude Code / claude-opus-4-6 (effort=low, max_output_tokens=4096)
- Base model: /home/user/models/Qwen3-1.7B-Base
- Not restored: model weights, generated training data, inspect-ai logs (see fork_manifest.json)
- Carried-over checkpoint index entries: 2 (metadata only)
