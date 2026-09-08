import json, random

all_samples = []

# Load original CodeAlpaca data
with open("artifacts/steps/step_002_improved_data/train_data.json") as f:
    all_samples.extend(json.load(f))

# Load synthetic parts (10x each)
for i in range(1, 4):
    with open(f"artifacts/steps/step_006_synth_data/part{i}.json") as f:
        all_samples.extend(json.load(f) * 10)

# Load thinking examples
with open("artifacts/steps/step_006_synth_data/thinking.json") as f:
    all_samples.extend(json.load(f))

random.seed(42)
random.shuffle(all_samples)

with open("artifacts/steps/step_006_synth_data/final_combined.json", "w") as f:
    json.dump(all_samples, f)
print(f"Total: {len(all_samples)}")
