import json

INST = "Read the following function signature and docstring, and fully implement the function described. Your response should only contain the code for this function.\n"
samples = []

funcs = [
('''from typing import List

def group_anagrams(strs: List[str]) -> List[List[str]]:
    """Group anagrams together.
    >>> sorted([sorted(g) for g in group_anagrams(["eat","tea","tan","ate","nat","bat"])])
    [['ate', 'eat', 'tea'], ['bat'], ['nat', 'tan']]
    """
''', '''    from collections import defaultdict
    groups = defaultdict(list)
    for s in strs:
        key = ''.join(sorted(s))
        groups[key].append(s)
    return list(groups.values())'''),

('''from typing import List

def longest_increasing_subsequence(nums: List[int]) -> int:
    """Length of longest increasing subsequence.
    >>> longest_increasing_subsequence([10, 9, 2, 5, 3, 7, 101, 18])
    4
    """
''', '''    if not nums:
        return 0
    dp = [1] * len(nums)
    for i in range(1, len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp)'''),

('''def climb_stairs(n: int) -> int:
    """Number of ways to climb n stairs (1 or 2 steps).
    >>> climb_stairs(4)
    5
    """
''', '''    if n <= 2:
        return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b'''),

('''def coin_change(coins: list, amount: int) -> int:
    """Minimum coins to make amount, -1 if impossible.
    >>> coin_change([1, 5, 10, 25], 30)
    2
    """
''', '''    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i:
                dp[i] = min(dp[i], dp[i - coin] + 1)
    return dp[amount] if dp[amount] != float('inf') else -1'''),

('''def max_profit(prices: list) -> int:
    """Best time to buy and sell stock once.
    >>> max_profit([7, 1, 5, 3, 6, 4])
    5
    """
''', '''    if not prices:
        return 0
    min_price = prices[0]
    max_profit = 0
    for price in prices[1:]:
        max_profit = max(max_profit, price - min_price)
        min_price = min(min_price, price)
    return max_profit'''),

('''from typing import List

def subsets(nums: List[int]) -> List[List[int]]:
    """Generate all subsets.
    >>> sorted(subsets([1, 2]))
    [[], [1], [1, 2], [2]]
    """
''', '''    result = [[]]
    for num in nums:
        result += [subset + [num] for subset in result]
    return result'''),

('''from typing import List

def permutations(nums: List[int]) -> List[List[int]]:
    """Generate all permutations.
    >>> sorted(permutations([1, 2, 3]))
    [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]
    """
''', '''    if len(nums) <= 1:
        return [nums]
    result = []
    for i, num in enumerate(nums):
        rest = nums[:i] + nums[i+1:]
        for perm in permutations(rest):
            result.append([num] + perm)
    return result'''),

('''def edit_distance(s1: str, s2: str) -> int:
    """Minimum edit distance between two strings.
    >>> edit_distance("kitten", "sitting")
    3
    """
''', '''    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    return dp[m][n]'''),

('''def knapsack(weights: list, values: list, capacity: int) -> int:
    """0/1 knapsack problem.
    >>> knapsack([2, 3, 4, 5], [3, 4, 5, 6], 5)
    7
    """
''', '''    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            dp[i][w] = dp[i-1][w]
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], dp[i-1][w-weights[i-1]] + values[i-1])
    return dp[n][capacity]'''),

('''def longest_palindrome_substring(s: str) -> str:
    """Find longest palindromic substring.
    >>> longest_palindrome_substring("babad")
    'bab'
    """
''', '''    if not s:
        return ""
    start, max_len = 0, 1
    def expand(l, r):
        nonlocal start, max_len
        while l >= 0 and r < len(s) and s[l] == s[r]:
            if r - l + 1 > max_len:
                start = l
                max_len = r - l + 1
            l -= 1
            r += 1
    for i in range(len(s)):
        expand(i, i)
        expand(i, i + 1)
    return s[start:start + max_len]'''),

('''from typing import List

def three_sum(nums: List[int]) -> List[List[int]]:
    """Find all unique triplets that sum to zero.
    >>> three_sum([-1, 0, 1, 2, -1, -4])
    [[-1, -1, 2], [-1, 0, 1]]
    """
''', '''    nums.sort()
    result = []
    for i in range(len(nums) - 2):
        if i > 0 and nums[i] == nums[i-1]:
            continue
        left, right = i + 1, len(nums) - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if total == 0:
                result.append([nums[i], nums[left], nums[right]])
                while left < right and nums[left] == nums[left+1]:
                    left += 1
                while left < right and nums[right] == nums[right-1]:
                    right -= 1
                left += 1
                right -= 1
            elif total < 0:
                left += 1
            else:
                right -= 1
    return result'''),

('''def decode_string(s: str) -> str:
    """Decode encoded string like "3[a2[c]]".
    >>> decode_string("3[a]2[bc]")
    'aaabcbc'
    """
''', '''    stack = []
    current = ""
    num = 0
    for c in s:
        if c.isdigit():
            num = num * 10 + int(c)
        elif c == '[':
            stack.append((current, num))
            current = ""
            num = 0
        elif c == ']':
            prev, count = stack.pop()
            current = prev + current * count
        else:
            current += c
    return current'''),

('''from typing import List, Tuple

def merge_intervals(intervals: List[List[int]]) -> List[List[int]]:
    """Merge overlapping intervals.
    >>> merge_intervals([[1,3],[2,6],[8,10],[15,18]])
    [[1, 6], [8, 10], [15, 18]]
    """
''', '''    if not intervals:
        return []
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged'''),

('''from typing import Optional, List

def generate_parentheses(n: int) -> List[str]:
    """Generate all valid parentheses combinations.
    >>> sorted(generate_parentheses(2))
    ['(())', '()()']
    """
''', '''    result = []
    def backtrack(s, open_count, close_count):
        if len(s) == 2 * n:
            result.append(s)
            return
        if open_count < n:
            backtrack(s + '(', open_count + 1, close_count)
        if close_count < open_count:
            backtrack(s + ')', open_count, close_count + 1)
    backtrack('', 0, 0)
    return result'''),

('''def atoi(s: str) -> int:
    """Convert string to integer (like C atoi).
    >>> atoi("   -42")
    -42
    >>> atoi("4193 with words")
    4193
    """
''', '''    s = s.strip()
    if not s:
        return 0
    sign = 1
    i = 0
    if s[0] in '+-':
        sign = -1 if s[0] == '-' else 1
        i = 1
    result = 0
    while i < len(s) and s[i].isdigit():
        result = result * 10 + int(s[i])
        i += 1
    result *= sign
    return max(min(result, 2**31 - 1), -(2**31))'''),

('''def zigzag_convert(s: str, numRows: int) -> str:
    """Zigzag conversion of string.
    >>> zigzag_convert("PAYPALISHIRING", 3)
    'PAHNAPLSIIGYIR'
    """
''', '''    if numRows <= 1 or numRows >= len(s):
        return s
    rows = [''] * numRows
    row, step = 0, 1
    for c in s:
        rows[row] += c
        if row == 0:
            step = 1
        elif row == numRows - 1:
            step = -1
        row += step
    return ''.join(rows)'''),

('''from typing import List

def trap_rain_water(height: List[int]) -> int:
    """Calculate trapped rain water.
    >>> trap_rain_water([0,1,0,2,1,0,1,3,2,1,2,1])
    6
    """
''', '''    if not height:
        return 0
    left, right = 0, len(height) - 1
    left_max = right_max = 0
    water = 0
    while left < right:
        if height[left] < height[right]:
            if height[left] >= left_max:
                left_max = height[left]
            else:
                water += left_max - height[left]
            left += 1
        else:
            if height[right] >= right_max:
                right_max = height[right]
            else:
                water += right_max - height[right]
            right -= 1
    return water'''),

('''from typing import List

def combination_sum(candidates: List[int], target: int) -> List[List[int]]:
    """Find combinations that sum to target (can reuse).
    >>> sorted(combination_sum([2, 3, 6, 7], 7))
    [[2, 2, 3], [7]]
    """
''', '''    result = []
    def backtrack(start, target, path):
        if target == 0:
            result.append(path[:])
            return
        for i in range(start, len(candidates)):
            if candidates[i] > target:
                break
            path.append(candidates[i])
            backtrack(i, target - candidates[i], path)
            path.pop()
    candidates.sort()
    backtrack(0, target, [])
    return result'''),

('''def is_valid_ip(s: str) -> bool:
    """Check if string is valid IPv4 address.
    >>> is_valid_ip("192.168.1.1")
    True
    >>> is_valid_ip("256.1.1.1")
    False
    """
''', '''    parts = s.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part or not part.isdigit():
            return False
        if len(part) > 1 and part[0] == '0':
            return False
        if int(part) > 255:
            return False
    return True'''),

('''from typing import List

def pascal_triangle(n: int) -> List[List[int]]:
    """Generate first n rows of Pascal's triangle.
    >>> pascal_triangle(4)
    [[1], [1, 1], [1, 2, 1], [1, 3, 3, 1]]
    """
''', '''    result = []
    for i in range(n):
        row = [1] * (i + 1)
        for j in range(1, i):
            row[j] = result[i-1][j-1] + result[i-1][j]
        result.append(row)
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

with open("artifacts/steps/step_006_synth_data/part3.json", "w") as f:
    json.dump(samples, f)
print(f"Part 3: {len(samples)} samples")
