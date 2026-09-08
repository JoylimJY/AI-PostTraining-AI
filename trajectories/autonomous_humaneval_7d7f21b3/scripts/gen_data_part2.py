import json

INST = "Read the following function signature and docstring, and fully implement the function described. Your response should only contain the code for this function.\n"
samples = []

funcs = [
# Sorting algorithms
('''from typing import List

def bubble_sort(lst: List[int]) -> List[int]:
    """Sort list using bubble sort.
    >>> bubble_sort([3, 1, 4, 1, 5])
    [1, 1, 3, 4, 5]
    """
''', '''    lst = lst.copy()
    n = len(lst)
    for i in range(n):
        for j in range(0, n-i-1):
            if lst[j] > lst[j+1]:
                lst[j], lst[j+1] = lst[j+1], lst[j]
    return lst'''),

('''from typing import List

def insertion_sort(lst: List[int]) -> List[int]:
    """Sort using insertion sort.
    >>> insertion_sort([3, 1, 4, 1, 5])
    [1, 1, 3, 4, 5]
    """
''', '''    lst = lst.copy()
    for i in range(1, len(lst)):
        key = lst[i]
        j = i - 1
        while j >= 0 and lst[j] > key:
            lst[j+1] = lst[j]
            j -= 1
        lst[j+1] = key
    return lst'''),

('''from typing import List

def quicksort(lst: List[int]) -> List[int]:
    """Sort using quicksort.
    >>> quicksort([3, 1, 4, 1, 5])
    [1, 1, 3, 4, 5]
    """
''', '''    if len(lst) <= 1:
        return lst
    pivot = lst[len(lst) // 2]
    left = [x for x in lst if x < pivot]
    middle = [x for x in lst if x == pivot]
    right = [x for x in lst if x > pivot]
    return quicksort(left) + middle + quicksort(right)'''),

# Search algorithms
('''from typing import List

def binary_search(arr: List[int], target: int) -> int:
    """Binary search, return index or -1.
    >>> binary_search([1, 3, 5, 7, 9], 5)
    2
    """
''', '''    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1'''),

('''from typing import List

def linear_search(arr: List, target) -> int:
    """Linear search, return index or -1.
    >>> linear_search([4, 2, 7, 1], 7)
    2
    """
''', '''    for i, val in enumerate(arr):
        if val == target:
            return i
    return -1'''),

# Data structure operations
('''def is_balanced(s: str) -> bool:
    """Check if parentheses are balanced.
    >>> is_balanced("(())")
    True
    >>> is_balanced("(()")
    False
    """
''', '''    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for c in s:
        if c in '([{':
            stack.append(c)
        elif c in ')]}':
            if not stack or stack[-1] != pairs[c]:
                return False
            stack.pop()
    return len(stack) == 0'''),

('''from typing import List

def two_sum(nums: List[int], target: int) -> List[int]:
    """Find indices of two numbers that sum to target.
    >>> two_sum([2, 7, 11, 15], 9)
    [0, 1]
    """
''', '''    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []'''),

('''from typing import List

def max_subarray_sum(nums: List[int]) -> int:
    """Maximum subarray sum (Kadane's algorithm).
    >>> max_subarray_sum([-2, 1, -3, 4, -1, 2, 1, -5, 4])
    6
    """
''', '''    if not nums:
        return 0
    max_sum = current = nums[0]
    for num in nums[1:]:
        current = max(num, current + num)
        max_sum = max(max_sum, current)
    return max_sum'''),

# More string operations
('''def longest_common_prefix(strs: list) -> str:
    """Find longest common prefix.
    >>> longest_common_prefix(["flower", "flow", "flight"])
    'fl'
    """
''', '''    if not strs:
        return ""
    prefix = strs[0]
    for s in strs[1:]:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    return prefix'''),

('''def valid_palindrome(s: str) -> bool:
    """Check if string is palindrome ignoring non-alphanumeric.
    >>> valid_palindrome("A man, a plan, a canal: Panama")
    True
    """
''', '''    cleaned = ''.join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]'''),

('''def count_substring(s: str, sub: str) -> int:
    """Count non-overlapping occurrences of sub in s.
    >>> count_substring("hello hello hello", "hello")
    3
    """
''', '''    return s.count(sub)'''),

('''def title_case(s: str) -> str:
    """Convert string to title case.
    >>> title_case("hello world")
    'Hello World'
    """
''', '''    return s.title()'''),

# Number theory
('''from typing import List

def sieve_of_eratosthenes(n: int) -> List[int]:
    """Return all primes up to n.
    >>> sieve_of_eratosthenes(10)
    [2, 3, 5, 7]
    """
''', '''    if n < 2:
        return []
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, n+1, i):
                is_prime[j] = False
    return [i for i in range(2, n+1) if is_prime[i]]'''),

('''def int_to_roman(num: int) -> str:
    """Convert integer to Roman numeral.
    >>> int_to_roman(1994)
    'MCMXCIV'
    """
''', '''    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
    result = ''
    for i in range(len(val)):
        while num >= val[i]:
            result += syms[i]
            num -= val[i]
    return result'''),

('''def roman_to_int(s: str) -> int:
    """Convert Roman numeral to integer.
    >>> roman_to_int('MCMXCIV')
    1994
    """
''', '''    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result = 0
    for i in range(len(s)):
        if i + 1 < len(s) and values[s[i]] < values[s[i+1]]:
            result -= values[s[i]]
        else:
            result += values[s[i]]
    return result'''),

('''def decimal_to_binary(n: int) -> str:
    """Convert decimal to binary string.
    >>> decimal_to_binary(10)
    '1010'
    """
''', '''    if n == 0:
        return '0'
    result = ''
    neg = n < 0
    n = abs(n)
    while n > 0:
        result = str(n % 2) + result
        n //= 2
    return ('-' if neg else '') + result'''),

('''def hex_to_decimal(hex_str: str) -> int:
    """Convert hex string to decimal.
    >>> hex_to_decimal('1A')
    26
    """
''', '''    return int(hex_str, 16)'''),

# More advanced list/array operations
('''from typing import List

def spiral_order(matrix: List[List[int]]) -> List[int]:
    """Return matrix elements in spiral order.
    >>> spiral_order([[1,2,3],[4,5,6],[7,8,9]])
    [1, 2, 3, 6, 9, 8, 7, 4, 5]
    """
''', '''    result = []
    if not matrix:
        return result
    top, bottom, left, right = 0, len(matrix)-1, 0, len(matrix[0])-1
    while top <= bottom and left <= right:
        for i in range(left, right+1):
            result.append(matrix[top][i])
        top += 1
        for i in range(top, bottom+1):
            result.append(matrix[i][right])
        right -= 1
        if top <= bottom:
            for i in range(right, left-1, -1):
                result.append(matrix[bottom][i])
            bottom -= 1
        if left <= right:
            for i in range(bottom, top-1, -1):
                result.append(matrix[i][left])
            left += 1
    return result'''),

('''from typing import List

def product_except_self(nums: List[int]) -> List[int]:
    """Product of array except self without division.
    >>> product_except_self([1, 2, 3, 4])
    [24, 12, 8, 6]
    """
''', '''    n = len(nums)
    result = [1] * n
    prefix = 1
    for i in range(n):
        result[i] = prefix
        prefix *= nums[i]
    suffix = 1
    for i in range(n-1, -1, -1):
        result[i] *= suffix
        suffix *= nums[i]
    return result'''),

('''from typing import List

def find_missing_number(nums: List[int]) -> int:
    """Find missing number in 0..n.
    >>> find_missing_number([3, 0, 1])
    2
    """
''', '''    n = len(nums)
    expected = n * (n + 1) // 2
    return expected - sum(nums)'''),

('''from typing import List

def move_zeros(nums: List[int]) -> List[int]:
    """Move all zeros to end preserving order.
    >>> move_zeros([0, 1, 0, 3, 12])
    [1, 3, 12, 0, 0]
    """
''', '''    result = [x for x in nums if x != 0]
    result.extend([0] * (len(nums) - len(result)))
    return result'''),
]

for prompt, solution in funcs:
    full = prompt + solution
    samples.append({"messages": [
        {"role": "user", "content": INST + prompt},
        {"role": "assistant", "content": f"```python\n{full}\n```"}
    ]})
    samples.append({"messages": [
        {"role": "user", "content": "Implement the following Python function:\n\n" + prompt},
        {"role": "assistant", "content": f"```python\n{full}\n```"}
    ]})

with open("artifacts/steps/step_006_synth_data/part2.json", "w") as f:
    json.dump(samples, f)
print(f"Part 2: {len(samples)} samples")
