import json, random

all_samples = []

# Load CodeAlpaca-based data
with open("artifacts/steps/step_002_improved_data/train_data.json") as f:
    all_samples.extend(json.load(f))

# Load synthetic parts
for i in range(1, 4):
    path = f"artifacts/steps/step_006_synth_data/part{i}.json"
    with open(path) as f:
        data = json.load(f)
        # Repeat synthetic examples 10x for emphasis
        all_samples.extend(data * 10)

random.seed(42)
random.shuffle(all_samples)

with open("artifacts/steps/step_006_synth_data/combined.json", "w") as f:
    json.dump(all_samples, f)
print(f"Total samples: {len(all_samples)}")
