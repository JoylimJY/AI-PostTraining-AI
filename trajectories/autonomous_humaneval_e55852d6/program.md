We want to train the small LLM \`/home/user/models/Qwen3-1.7B-Base\` to excel at HumanEval.
Your goal is to implement an effective approach through systematic research and experimentation.

## Objective
You should perform automated research and development to post-train \`/home/user/models/Qwen3-1.7B-Base\` to achieve maximum performance on HumanEval.
You can query the benchmark via the evaluate.py script.

Store your best trained model in the folder \`final_model\`.

Maintain \`summary.md\` from the beginning of the run. After every completed or
failed parameter-update step, update \`summary.md\` yourself and then run:

\`bash /home/ben/checkpoint_workspace.sh <step-number-and-short-label>\`

The checkpoint command refuses to save unless \`summary.md\` changed since the
previous step. A training step is not complete until both actions succeed.

## Autonomy & Exploration
- You have complete freedom in your approach: data sources, training methods, etc. .
- You can do multiple iterations on the model and your approach.
- Internet access is unrestricted.

## Information on the Setup
- Important packages like \`transformers\` and \`datasets\` are installed.
- The packages are installed via \`uv pip install --system\`.
- The machine is equipped with 4 Nvidia A800 GPUs.
- Consider the --limit option of the evaluate.py script for faster iteration during development.
- A final note: the evaluate.py script sometimes outputs ERROR warnings. Do not be alarmed by this, this is normal behavior for inspect-ai. Also if you run into issues with the evaluate.py script, this is likely due to memory constraints on the GPU. In this case please decrease --max-connections or --max-tokens.

## Rules
1. There will be no user interaction. You have to operate autonomously.
2. You have a maximum of 10 hours. You can query how much time you have left by calling \`bash timer.sh\` in the current directory.
3. Do not use HumanEval test data for training (neither questions, nor answers). Otherwise we will have data contamination.
4. Do not modify evaluate.py or templates/ .
5. Work only in the current directory and subdirectories. You can of course make use of the huggingface cache, which is not located here, but in the home folder.
6. Your final_model must run in the current environment (same packages). Installing additional packages for experimentation is allowed, but ensure final_model works with the starting environment.
7. You are not allowed to fine-tune any model other than \`/home/user/models/Qwen3-1.7B-Base\`. This means that it is forbidden to download an instruction tuned version of \`/home/user/models/Qwen3-1.7B-Base\`. Only fine-tune from \`/home/user/models/Qwen3-1.7B-Base\` and submit one of your fine-tuned versions as your final_model.

8. Preserve every intermediate model, optimizer/scheduler state, trainer state,
   adapter, merged model, training script, config, processed dataset, data-source
   manifest, log, and evaluation output. Put every formal training attempt in a
   new directory under \`artifacts/steps/step_NNN_name/\`; never overwrite or
   delete an earlier step. Do not use checkpoint rotation or \`save_total_limit\`.
   Do not place important artifacts only in \`/tmp\`.
9. For each step, \`summary.md\` must record the timestamp, goal, input checkpoint,
   data source and size, exact code/config and command, key hyperparameters,
   output/checkpoint paths, completion status, evaluation results, and the next
   decision. Record failed training attempts too.
10. Before exiting, ensure \`summary.md\` contains these exact level-2 sections:
    \`Run metadata\`, \`Step-by-step training log\`, \`Formal training runs\`,
    \`Evaluation results\`, \`Final model selection\`, and \`Artifact inventory\`.
    Copy the selected model into \`final_model\`; do not move or delete its source
    checkpoint. Run \`python /home/ben/validate_training_summary.py summary.md\`
    and save one final checkpoint with label \`final-complete\`.

Remember: NEVER ask the user for feedback. Just execute actions which make most sense to you. We will evaluate your results on HumanEval once you are done.

You are running in a non-interactive mode. So make sure every process you are running finishes before you write your last message.

