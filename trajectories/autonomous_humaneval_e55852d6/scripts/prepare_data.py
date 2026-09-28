"""Prepare training data for HumanEval fine-tuning."""
import json
import random

# Load CodeAlpaca-20k
with open("/tmp/datasets/code_alpaca_20k.json") as f:
    code_alpaca = json.load(f)

print(f"Total CodeAlpaca samples: {len(code_alpaca)}")

# Filter for Python-related samples and general code tasks
python_keywords = ['python', 'def ', 'class ', 'import ', 'print(', 'list', 'dict', 'tuple', 
                   'string', 'array', 'function', 'return', 'for ', 'while ', 'if ', 
                   'algorithm', 'sort', 'search', 'fibonacci', 'factorial', 'prime',
                   'palindrome', 'reverse', 'sum', 'max', 'min', 'count', 'average',
                   'matrix', 'tree', 'linked list', 'stack', 'queue', 'recursive',
                   'binary', 'implement', 'write a', 'create a', 'design a', 'develop',
                   'calculate', 'compute', 'generate', 'find', 'check', 'valid',
                   'convert', 'parse', 'format', 'encode', 'decode']

def is_python_related(sample):
    """Check if a sample is Python-related."""
    text = (sample.get('instruction', '') + ' ' + sample.get('output', '') + ' ' + sample.get('input', '')).lower()
    # Exclude non-Python languages
    non_python = ['java ', 'javascript', 'c++', 'c#', 'ruby', 'swift', 'kotlin', 'rust',
                  'typescript', 'go ', 'golang', 'scala', 'perl', 'php ', 'html', 'css',
                  'sql', 'bash', 'shell', 'powershell', 'r ', 'matlab']
    
    for kw in non_python:
        if kw in text and 'python' not in text:
            return False
    
    # Check for Python indicators
    output = sample.get('output', '')
    if 'def ' in output or 'import ' in output or 'print(' in output:
        return True
    
    for kw in python_keywords:
        if kw in text:
            return True
    
    return False

python_samples = [s for s in code_alpaca if is_python_related(s)]
print(f"Python-related samples: {len(python_samples)}")

# Format into chat format for SFT
SYSTEM_PROMPT = "You are a helpful coding assistant. When asked to write code, provide clean, correct Python code."

def format_for_training(sample):
    """Format a sample into Qwen3 chat format."""
    instruction = sample['instruction']
    input_text = sample.get('input', '').strip()
    output = sample['output']
    
    if input_text:
        user_message = f"{instruction}\n\n{input_text}"
    else:
        user_message = instruction
    
    # Ensure output has proper Python code formatting
    if 'def ' in output or 'class ' in output or 'import ' in output:
        if not output.startswith('```'):
            assistant_message = f"```python\n{output}\n```"
        else:
            assistant_message = output
    else:
        assistant_message = output
    
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ]
    }

# Also create HumanEval-style samples
# Format: "Read the following function signature and docstring, and fully implement the function described."
HUMANEVAL_INSTRUCTION = """Read the following function signature and docstring, and fully implement the function described. Your response should only contain the code for this function.\n"""

def create_humaneval_style_samples():
    """Create training samples that mimic HumanEval format."""
    samples = []
    
    # Create function completion tasks from CodeAlpaca
    for s in python_samples:
        output = s['output']
        # Look for samples that contain function definitions
        if 'def ' in output:
            lines = output.split('\n')
            # Find the function signature
            for i, line in enumerate(lines):
                if line.strip().startswith('def '):
                    # Extract signature and docstring
                    sig_lines = [line]
                    j = i + 1
                    in_docstring = False
                    docstring_lines = []
                    while j < len(lines):
                        l = lines[j].strip()
                        if '"""' in l or "'''" in l:
                            if in_docstring:
                                docstring_lines.append(lines[j])
                                in_docstring = False
                                break
                            else:
                                in_docstring = True
                                docstring_lines.append(lines[j])
                        elif in_docstring:
                            docstring_lines.append(lines[j])
                        else:
                            break
                        j += 1
                    
                    if docstring_lines:
                        prompt = '\n'.join(sig_lines + docstring_lines) + '\n'
                        body = '\n'.join(lines[j+1:])
                        if body.strip():
                            sample = {
                                "messages": [
                                    {"role": "user", "content": HUMANEVAL_INSTRUCTION + prompt},
                                    {"role": "assistant", "content": f"```python\n{output}\n```"}
                                ]
                            }
                            samples.append(sample)
                    break
    
    return samples

# Format all samples
formatted_samples = [format_for_training(s) for s in python_samples]
humaneval_style = create_humaneval_style_samples()

print(f"Formatted samples: {len(formatted_samples)}")
print(f"HumanEval-style samples: {len(humaneval_style)}")

# Combine and add more training variety
all_samples = formatted_samples + humaneval_style

# Also add the non-Python samples (general coding ability helps)
non_python = [s for s in code_alpaca if s not in python_samples]
general_formatted = [format_for_training(s) for s in non_python[:2000]]  # Keep some general coding
all_samples.extend(general_formatted)

random.seed(42)
random.shuffle(all_samples)

print(f"Total training samples: {len(all_samples)}")

# Save
output_path = "artifacts/steps/step_001_sft_data/train_data.json"
import os
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w') as f:
    json.dump(all_samples, f, indent=2)
print(f"Saved to {output_path}")

# Show a sample
print("\n--- Sample 0 ---")
print(json.dumps(all_samples[0], indent=2)[:500])
