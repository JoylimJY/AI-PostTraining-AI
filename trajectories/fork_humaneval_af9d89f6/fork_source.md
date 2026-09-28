# Forked run (from an archived trajectory, at a chosen node)

- Run: claude_opus46_humaneval_qwen3_1_7b_20260902_114122_fork_run8_20260924_103824
- Archive: /home/user/ptb/opus46/trajectories_opus46/autonomous_humaneval_7d7f21b3
- Source run: claude_opus46_humaneval_qwen3_1_7b_20260902_114122 (budget 10 h, agent claude-opus-4-6)
- Fork node: Run 8 (step_008_final_train: full SFT from base on the 17.4K thinking-augmented data, 8 epochs) and its first full 164-problem evaluation (about 5h14m into the source run)
- Fork state: trajectory.jsonl lines 1..(result of the tool call on line 4687); see fork_source/fork_manifest.json
- Forked at: 2026-09-24T10:38:27+0800
- Fresh time budget: 5 hours
- Hint given to the agent: Please evaluate whether the current strategy needs adjustment.
- Benchmark: humaneval
- Agent: Claude Code / claude-opus-4-6 (effort=low, max_output_tokens=4096)
- Base model: /home/user/models/Qwen3-1.7B-Base
- Not restored: model weights, generated training data, inspect-ai logs (see fork_manifest.json)
- Carried-over checkpoint index entries: 12 (metadata only)
