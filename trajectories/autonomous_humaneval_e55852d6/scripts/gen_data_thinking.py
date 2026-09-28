import json, random

# Create training data with thinking process
INST = "Read the following function signature and docstring, and fully implement the function described. Your response should only contain the code for this function.\n"

samples = []

# Each entry: (prompt, thinking, code)
funcs_with_thinking = [
('''from typing import List

def separate_paren_groups(paren_string: str) -> List[str]:
    """Separate groups of balanced parentheses.
    >>> separate_paren_groups('( ) (( )) (( )( ))')
    ['()', '(())', '(()())']
    """
''',
"I need to separate balanced parentheses groups. I'll track the depth counter - when it goes back to 0, I've found a complete group.",
'''    result = []
    current = ''
    depth = 0
    for c in paren_string:
        if c == '(':
            current += c
            depth += 1
        elif c == ')':
            current += c
            depth -= 1
            if depth == 0:
                result.append(current)
                current = ''
    return result'''),

('''from typing import List

def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """Check if any two numbers are closer than threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    """
''',
"I need to compare every pair of numbers. I can sort first for efficiency, but a simple nested loop works too.",
'''    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if abs(numbers[i] - numbers[j]) < threshold:
                return True
    return False'''),

('''def make_palindrome(string: str) -> str:
    """Find shortest palindrome starting with given string.
    >>> make_palindrome('')
    ''
    >>> make_palindrome('cat')
    'catac'
    """
''',
"Find the longest suffix that is a palindrome, then append the reverse of the prefix before it.",
'''    if not string:
        return ''
    for i in range(len(string)):
        suffix = string[i:]
        if suffix == suffix[::-1]:
            prefix = string[:i]
            return string + prefix[::-1]
    return string + string[:-1][::-1]'''),

('''from typing import List

def below_zero(operations: List[int]) -> bool:
    """Check if balance goes below zero during operations.
    >>> below_zero([1, 2, -3, 1, 2, -2])
    False
    >>> below_zero([1, 2, -4, 5, 6])
    True
    """
''',
"Start with balance 0, apply each operation, check if it ever goes below zero.",
'''    balance = 0
    for op in operations:
        balance += op
        if balance < 0:
            return True
    return False'''),

('''from typing import List

def mean_absolute_deviation(numbers: List[float]) -> float:
    """Calculate mean absolute deviation.
    >>> mean_absolute_deviation([1.0, 2.0, 3.0, 4.0])
    1.0
    """
''',
"First calculate the mean, then the average of absolute deviations from the mean.",
'''    mean = sum(numbers) / len(numbers)
    return sum(abs(x - mean) for x in numbers) / len(numbers)'''),

('''from typing import List

def intersperse(numbers: List[int], delimeter: int) -> List[int]:
    """Insert delimeter between every two elements.
    >>> intersperse([1, 2, 3], 4)
    [1, 4, 2, 4, 3]
    """
''',
"I need to insert the delimiter between elements. I can build the result by adding each element followed by the delimiter, then remove the last delimiter.",
'''    if not numbers:
        return []
    result = []
    for i, num in enumerate(numbers):
        result.append(num)
        if i < len(numbers) - 1:
            result.append(delimeter)
    return result'''),

('''from typing import List

def parse_nested_parens(paren_string: str) -> List[int]:
    """Return max nesting depth for each group of parens.
    >>> parse_nested_parens('(()()) ((())) () ((())()())')
    [2, 3, 1, 3]
    """
''',
"Split by spaces to get groups, then for each group track depth and record maximum.",
'''    groups = paren_string.split()
    result = []
    for group in groups:
        depth = 0
        max_depth = 0
        for c in group:
            if c == '(':
                depth += 1
                max_depth = max(max_depth, depth)
            elif c == ')':
                depth -= 1
        result.append(max_depth)
    return result'''),

('''from typing import List

def filter_by_substring(strings: List[str], substring: str) -> List[str]:
    """Filter strings that contain substring.
    >>> filter_by_substring(['abc', 'bacd', 'cde', 'array'], 'a')
    ['abc', 'bacd', 'array']
    """
''',
"Simple filter - keep strings where substring is found.",
'''    return [s for s in strings if substring in s]'''),

('''from typing import List, Tuple

def sum_product(numbers: List[int]) -> Tuple[int, int]:
    """Return sum and product of list of integers.
    >>> sum_product([1, 2, 3, 4])
    (10, 24)
    """
''',
"Calculate sum and product separately.",
'''    total = 0
    product = 1
    for n in numbers:
        total += n
        product *= n
    return (total, product)'''),

('''from typing import List

def rolling_max(numbers: List[int]) -> List[int]:
    """Return rolling maximum element at each position.
    >>> rolling_max([1, 2, 3, 2, 3, 4, 2])
    [1, 2, 3, 3, 3, 4, 4]
    """
''',
"Track the running maximum as we iterate through the list.",
'''    result = []
    current_max = float('-inf')
    for n in numbers:
        current_max = max(current_max, n)
        result.append(current_max)
    return result'''),

('''def string_xor(a: str, b: str) -> str:
    """XOR two binary strings.
    >>> string_xor('010', '110')
    '100'
    """
''',
"XOR each pair of corresponding bits.",
'''    return ''.join('0' if x == y else '1' for x, y in zip(a, b))'''),

('''from typing import List, Optional

def longest(strings: List[str]) -> Optional[str]:
    """Return longest string, or None if empty.
    >>> longest(['a', 'bb', 'ccc'])
    'ccc'
    """
''',
"Find the string with maximum length.",
'''    if not strings:
        return None
    return max(strings, key=len)'''),

('''def greatest_common_divisor(a: int, b: int) -> int:
    """Return GCD using Euclidean algorithm.
    >>> greatest_common_divisor(3, 5)
    1
    >>> greatest_common_divisor(25, 15)
    5
    """
''',
"Use Euclidean algorithm: gcd(a,b) = gcd(b, a%b).",
'''    while b:
        a, b = b, a % b
    return a'''),

('''from typing import List

def all_prefixes(string: str) -> List[str]:
    """Return all prefixes from shortest to longest.
    >>> all_prefixes('abc')
    ['a', 'ab', 'abc']
    """
''',
"Generate substrings from index 0 to each position.",
'''    return [string[:i+1] for i in range(len(string))]'''),

('''def string_sequence(n: int) -> str:
    """Return space-delimited string of 0 to n.
    >>> string_sequence(5)
    '0 1 2 3 4 5'
    """
''',
"Generate numbers 0 to n and join with spaces.",
'''    return ' '.join(str(i) for i in range(n + 1))'''),

('''def count_distinct_characters(string: str) -> int:
    """Count distinct characters (case-insensitive).
    >>> count_distinct_characters('xyzXYZ')
    3
    """
''',
"Convert to lowercase and count unique characters.",
'''    return len(set(string.lower()))'''),

('''from typing import List

def parse_music(music_string: str) -> List[int]:
    """Parse music string where 'o' is 4 beats, 'o|' is 2, '.|' is 1.
    >>> parse_music('o o| .| o| o| .| .| .| .| o o')
    [4, 2, 1, 2, 2, 1, 1, 1, 1, 4, 4]
    """
''',
"Split by spaces, map each note to its beat count.",
'''    if not music_string:
        return []
    notes = music_string.split()
    mapping = {'o': 4, 'o|': 2, '.|': 1}
    return [mapping[note] for note in notes]'''),

('''def how_many_times(string: str, substring: str) -> int:
    """Count overlapping occurrences of substring.
    >>> how_many_times('aaa', 'aa')
    2
    """
''',
"Check each position for a match.",
'''    count = 0
    for i in range(len(string) - len(substring) + 1):
        if string[i:i+len(substring)] == substring:
            count += 1
    return count'''),

('''from typing import List

def sort_numbers(numbers: str) -> str:
    """Sort space-delimited number words.
    >>> sort_numbers('three one five')
    'one three five'
    """
''',
"Map words to numbers, sort, map back.",
'''    value_map = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9
    }
    if not numbers:
        return ''
    words = numbers.split()
    words.sort(key=lambda w: value_map[w])
    return ' '.join(words)'''),

('''from typing import List

def find_closest_elements(numbers: List[float]) -> tuple:
    """Find two closest elements.
    >>> find_closest_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.2])
    (2.0, 2.2)
    """
''',
"Compare all pairs, track the minimum distance.",
'''    closest = None
    min_dist = float('inf')
    for i in range(len(numbers)):
        for j in range(i+1, len(numbers)):
            dist = abs(numbers[i] - numbers[j])
            if dist < min_dist:
                min_dist = dist
                closest = tuple(sorted([numbers[i], numbers[j]]))
    return closest'''),
]

for prompt, thinking, solution in funcs_with_thinking:
    full = prompt + solution
    # Version with thinking
    samples.append({"messages": [
        {"role": "user", "content": INST + prompt},
        {"role": "assistant", "content": f"<think>\n{thinking}\n</think>\n\n```python\n{full}\n```"}
    ]})
    # Version without thinking (direct)
    samples.append({"messages": [
        {"role": "user", "content": INST + prompt},
        {"role": "assistant", "content": f"```python\n{full}\n```"}
    ]})
    # Version with different instruction
    samples.append({"messages": [
        {"role": "user", "content": "Complete the following Python function:\n\n" + prompt},
        {"role": "assistant", "content": f"<think>\n{thinking}\n</think>\n\n```python\n{full}\n```"}
    ]})

# Repeat 5x for emphasis
samples = samples * 5
random.seed(42)
random.shuffle(samples)

with open("artifacts/steps/step_006_synth_data/thinking.json", "w") as f:
    json.dump(samples, f)
print(f"Thinking samples: {len(samples)}")
