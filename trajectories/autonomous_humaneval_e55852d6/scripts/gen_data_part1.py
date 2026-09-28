import json, random

INST = "Read the following function signature and docstring, and fully implement the function described. Your response should only contain the code for this function.\n"

samples = []

funcs = [
# String operations
('''def count_upper(s: str) -> int:
    """Count the number of uppercase letters in s.
    >>> count_upper("Hello World")
    2
    >>> count_upper("abc")
    0
    """
''', '''    return sum(1 for c in s if c.isupper())'''),

('''def count_lower(s: str) -> int:
    """Count the number of lowercase letters in s."""
''', '''    return sum(1 for c in s if c.islower())'''),

('''def capitalize_words(s: str) -> str:
    """Capitalize the first letter of each word.
    >>> capitalize_words("hello world")
    'Hello World'
    """
''', '''    return ' '.join(w.capitalize() for w in s.split())'''),

('''def remove_vowels(text: str) -> str:
    """Remove all vowels from text.
    >>> remove_vowels("hello")
    'hll'
    """
''', '''    return ''.join(c for c in text if c.lower() not in 'aeiou')'''),

('''def reverse_words(s: str) -> str:
    """Reverse the order of words in s.
    >>> reverse_words("hello world")
    'world hello'
    """
''', '''    return ' '.join(s.split()[::-1])'''),

('''def is_anagram(s1: str, s2: str) -> bool:
    """Check if s1 and s2 are anagrams.
    >>> is_anagram("listen", "silent")
    True
    """
''', '''    return sorted(s1.lower()) == sorted(s2.lower())'''),

('''def caesar_cipher(text: str, shift: int) -> str:
    """Apply Caesar cipher with given shift.
    >>> caesar_cipher("abc", 1)
    'bcd'
    """
''', '''    result = []
    for c in text:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            result.append(chr((ord(c) - base + shift) % 26 + base))
        else:
            result.append(c)
    return ''.join(result)'''),

('''def longest_word(s: str) -> str:
    """Return the longest word in string s.
    >>> longest_word("I love programming")
    'programming'
    """
''', '''    words = s.split()
    return max(words, key=len) if words else ""'''),

('''def char_frequency(s: str) -> dict:
    """Return a dict mapping each character to its frequency.
    >>> char_frequency("aab")
    {'a': 2, 'b': 1}
    """
''', '''    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    return freq'''),

('''def compress_string(s: str) -> str:
    """Run-length encoding of string.
    >>> compress_string("aaabbc")
    'a3b2c1'
    """
''', '''    if not s:
        return ""
    result = []
    count = 1
    for i in range(1, len(s)):
        if s[i] == s[i-1]:
            count += 1
        else:
            result.append(s[i-1] + str(count))
            count = 1
    result.append(s[-1] + str(count))
    return ''.join(result)'''),

# Math operations
('''def gcd(a: int, b: int) -> int:
    """Greatest common divisor.
    >>> gcd(12, 8)
    4
    """
''', '''    while b:
        a, b = b, a % b
    return a'''),

('''def lcm(a: int, b: int) -> int:
    """Least common multiple.
    >>> lcm(4, 6)
    12
    """
''', '''    def gcd(x, y):
        while y:
            x, y = y, x % y
        return x
    return abs(a * b) // gcd(a, b)'''),

('''def is_prime(n: int) -> bool:
    """Check if n is prime.
    >>> is_prime(7)
    True
    >>> is_prime(4)
    False
    """
''', '''    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True'''),

('''def prime_factors(n: int) -> list:
    """Return prime factors of n.
    >>> prime_factors(12)
    [2, 2, 3]
    """
''', '''    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors'''),

('''def fibonacci(n: int) -> int:
    """Return nth Fibonacci number.
    >>> fibonacci(6)
    8
    """
''', '''    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b'''),

('''def factorial(n: int) -> int:
    """Return n factorial.
    >>> factorial(5)
    120
    """
''', '''    if n <= 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result'''),

('''def power(base: float, exp: int) -> float:
    """Calculate base^exp using fast exponentiation.
    >>> power(2, 10)
    1024
    """
''', '''    if exp == 0:
        return 1
    if exp < 0:
        return 1 / power(base, -exp)
    if exp % 2 == 0:
        half = power(base, exp // 2)
        return half * half
    return base * power(base, exp - 1)'''),

('''def digit_sum(n: int) -> int:
    """Sum of digits of n.
    >>> digit_sum(123)
    6
    """
''', '''    return sum(int(d) for d in str(abs(n)))'''),

('''def num_digits(n: int) -> int:
    """Count digits in n.
    >>> num_digits(12345)
    5
    """
''', '''    if n == 0:
        return 1
    count = 0
    n = abs(n)
    while n > 0:
        count += 1
        n //= 10
    return count'''),

('''def is_perfect_square(n: int) -> bool:
    """Check if n is a perfect square.
    >>> is_perfect_square(16)
    True
    >>> is_perfect_square(15)
    False
    """
''', '''    if n < 0:
        return False
    root = int(n ** 0.5)
    return root * root == n'''),

# List operations
('''from typing import List

def flatten(lst: List) -> List:
    """Flatten a nested list.
    >>> flatten([1, [2, 3], [4, [5]]])
    [1, 2, 3, 4, 5]
    """
''', '''    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result'''),

('''from typing import List

def remove_duplicates(lst: List) -> List:
    """Remove duplicates preserving order.
    >>> remove_duplicates([1, 2, 2, 3, 1])
    [1, 2, 3]
    """
''', '''    seen = set()
    result = []
    for x in lst:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result'''),

('''from typing import List

def chunk_list(lst: List, size: int) -> List[List]:
    """Split list into chunks of given size.
    >>> chunk_list([1,2,3,4,5], 2)
    [[1, 2], [3, 4], [5]]
    """
''', '''    return [lst[i:i+size] for i in range(0, len(lst), size)]'''),

('''from typing import List

def interleave(lst1: List, lst2: List) -> List:
    """Interleave two lists.
    >>> interleave([1, 3, 5], [2, 4, 6])
    [1, 2, 3, 4, 5, 6]
    """
''', '''    result = []
    i = j = 0
    while i < len(lst1) and j < len(lst2):
        result.append(lst1[i])
        result.append(lst2[j])
        i += 1
        j += 1
    result.extend(lst1[i:])
    result.extend(lst2[j:])
    return result'''),

('''from typing import List

def rotate_list(lst: List, k: int) -> List:
    """Rotate list right by k positions.
    >>> rotate_list([1, 2, 3, 4, 5], 2)
    [4, 5, 1, 2, 3]
    """
''', '''    if not lst:
        return lst
    k = k % len(lst)
    return lst[-k:] + lst[:-k]'''),

('''from typing import List

def second_largest(nums: List[int]) -> int:
    """Return second largest element.
    >>> second_largest([1, 3, 5, 2, 4])
    4
    """
''', '''    unique = list(set(nums))
    unique.sort()
    return unique[-2] if len(unique) >= 2 else None'''),

('''from typing import List

def running_sum(nums: List[int]) -> List[int]:
    """Return running sum of list.
    >>> running_sum([1, 2, 3, 4])
    [1, 3, 6, 10]
    """
''', '''    result = []
    total = 0
    for n in nums:
        total += n
        result.append(total)
    return result'''),

('''from typing import List

def merge_sorted(lst1: List[int], lst2: List[int]) -> List[int]:
    """Merge two sorted lists.
    >>> merge_sorted([1, 3, 5], [2, 4, 6])
    [1, 2, 3, 4, 5, 6]
    """
''', '''    result = []
    i = j = 0
    while i < len(lst1) and j < len(lst2):
        if lst1[i] <= lst2[j]:
            result.append(lst1[i])
            i += 1
        else:
            result.append(lst2[j])
            j += 1
    result.extend(lst1[i:])
    result.extend(lst2[j:])
    return result'''),

('''from typing import List

def most_frequent(lst: List) -> any:
    """Return most frequent element.
    >>> most_frequent([1, 2, 2, 3, 3, 3])
    3
    """
''', '''    from collections import Counter
    return Counter(lst).most_common(1)[0][0]'''),

('''from typing import List

def matrix_transpose(matrix: List[List[int]]) -> List[List[int]]:
    """Transpose a matrix.
    >>> matrix_transpose([[1, 2], [3, 4]])
    [[1, 3], [2, 4]]
    """
''', '''    if not matrix:
        return []
    return [[row[i] for row in matrix] for i in range(len(matrix[0]))]'''),
]

for prompt, solution in funcs:
    full = prompt + solution
    samples.append({"messages": [
        {"role": "user", "content": INST + prompt},
        {"role": "assistant", "content": f"```python\n{full}\n```"}
    ]})
    # Also add direct instruction variant
    samples.append({"messages": [
        {"role": "user", "content": "Implement the following Python function:\n\n" + prompt},
        {"role": "assistant", "content": f"```python\n{full}\n```"}
    ]})

with open("artifacts/steps/step_006_synth_data/part1.json", "w") as f:
    json.dump(samples, f)
print(f"Part 1: {len(samples)} samples")
