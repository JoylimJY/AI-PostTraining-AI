import json, random

all_samples = []

# Load synthetic parts only
for i in range(1, 4):
    with open(f"artifacts/steps/step_006_synth_data/part{i}.json") as f:
        all_samples.extend(json.load(f))

# Load thinking examples
with open("artifacts/steps/step_006_synth_data/thinking.json") as f:
    all_samples.extend(json.load(f))

# Repeat everything 20x  
all_samples = all_samples * 20
random.seed(42)
random.shuffle(all_samples)

with open("artifacts/steps/step_006_synth_data/synth_only.json", "w") as f:
    json.dump(all_samples, f)
print(f"Total: {len(all_samples)}")
