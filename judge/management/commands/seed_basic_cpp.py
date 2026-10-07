import os
import zipfile
import yaml
from django.core.management.base import BaseCommand
from django.conf import settings
from judge.models import (
    Problem,
    ProblemGroup,
    ProblemType,
    ProblemData,
    ProblemTestCase,
    Language,
)

PROBLEMS = [
    {
        "code": "cpp01_sum",
        "name": "Sum of Two Numbers",
        "type": "Mathematics",
        "group": "Beginner",
        "points": 100,
        "time_limit": 1.0,
        "memory_limit": 262144,
        "description": """## Problem Statement
Given two integers $a$ and $b$, write a program to calculate and display their sum: $S = a + b$.

### Input Specification
The input consists of a single line containing two space-separated integers $a$ and $b$ ($-10^9 \\le a, b \\le 10^9$).

### Output Specification
Print a single integer representing the sum $a + b$.

### Sample Input
```
12 34
```

### Sample Output
```
46
```

### Explanation
$12 + 34 = 46$.
""",
        "tests": [
            ("3 5\n", "8\n"),
            ("-10 25\n", "15\n"),
            ("0 0\n", "0\n"),
            ("-500000000 -400000000\n", "-900000000\n"),
            ("1000000000 1000000000\n", "2000000000\n"),
        ],
    },
    {
        "code": "cpp02_even_odd",
        "name": "Even or Odd Number",
        "type": "Implementation",
        "group": "Beginner",
        "points": 100,
        "time_limit": 1.0,
        "memory_limit": 262144,
        "description": """## Problem Statement
Given an integer $n$, determine whether it is an **EVEN** number or an **ODD** number.

### Input Specification
A single line containing an integer $n$ ($-10^9 \\le n \\le 10^9$).

### Output Specification
Print `EVEN` if $n$ is divisible by 2, or `ODD` otherwise.

### Sample Input 1
```
7
```
### Sample Output 1
```
ODD
```

### Sample Input 2
```
-14
```
### Sample Output 2
```
EVEN
```
""",
        "tests": [
            ("7\n", "ODD\n"),
            ("10\n", "EVEN\n"),
            ("0\n", "EVEN\n"),
            ("-13\n", "ODD\n"),
            ("1000000000\n", "EVEN\n"),
        ],
    },
    {
        "code": "cpp03_factorial",
        "name": "Factorial Calculation",
        "type": "Mathematics",
        "group": "Beginner",
        "points": 100,
        "time_limit": 1.0,
        "memory_limit": 262144,
        "description": """## Problem Statement
The factorial of a non-negative integer $n$, denoted by $n!$, is the product of all positive integers less than or equal to $n$.
By definition, $0! = 1$.
Given $n$, calculate the value of $n!$.

### Input Specification
A single line containing an integer $n$ ($0 \\le n \\le 20$).

### Output Specification
Print a single integer representing $n!$.

### Sample Input
```
5
```

### Sample Output
```
120
```

### Explanation
$5! = 1 \\times 2 \\times 3 \\times 4 \\times 5 = 120$. Note that for $n = 20$, the answer can be as large as $\\approx 2.43 \\times 10^{18}$, which requires a 64-bit integer (`long long` in C++).
""",
        "tests": [
            ("0\n", "1\n"),
            ("1\n", "1\n"),
            ("5\n", "120\n"),
            ("10\n", "3628800\n"),
            ("20\n", "2432902008176640000\n"),
        ],
    },
    {
        "code": "cpp04_max3",
        "name": "Maximum of Three Numbers",
        "type": "Implementation",
        "group": "Beginner",
        "points": 100,
        "time_limit": 1.0,
        "memory_limit": 262144,
        "description": """## Problem Statement
Given three integers $a$, $b$, and $c$, determine and print the maximum value among them.

### Input Specification
A single line containing three space-separated integers $a, b, c$ ($-10^9 \\le a, b, c \\le 10^9$).

### Output Specification
Print the maximum value among $a$, $b$, and $c$.

### Sample Input
```
15 42 27
```

### Sample Output
```
42
```
""",
        "tests": [
            ("15 42 27\n", "42\n"),
            ("-5 -12 -1\n", "-1\n"),
            ("100 100 50\n", "100\n"),
            ("0 0 0\n", "0\n"),
            ("1000000000 999999999 5\n", "1000000000\n"),
        ],
    },
    {
        "code": "cpp05_prime",
        "name": "Prime Number Check",
        "type": "Mathematics",
        "group": "Beginner",
        "points": 100,
        "time_limit": 1.0,
        "memory_limit": 262144,
        "description": """## Problem Statement
A prime number is a natural number greater than 1 that has no positive divisors other than 1 and itself.
Given an integer $n$, check whether $n$ is a prime number.

### Input Specification
A single line containing an integer $n$ ($1 \\le n \\le 10^9$).

### Output Specification
Print `YES` if $n$ is prime, or `NO` if it is not.

### Sample Input 1
```
17
```
### Sample Output 1
```
YES
```

### Sample Input 2
```
1
```
### Sample Output 2
```
NO
```
""",
        "tests": [
            ("1\n", "NO\n"),
            ("2\n", "YES\n"),
            ("17\n", "YES\n"),
            ("100\n", "NO\n"),
            ("999999937\n", "YES\n"),
        ],
    },
    {
        "code": "cpp06_reverse_array",
        "name": "Reverse an Array",
        "type": "Data Structures",
        "group": "Beginner",
        "points": 100,
        "time_limit": 1.0,
        "memory_limit": 262144,
        "description": """## Problem Statement
Given an array of $n$ integers, print all elements in reverse order (from the last element to the first element).

### Input Specification
* The first line contains an integer $n$ ($1 \\le n \\le 10^5$), representing the number of elements.
* The second line contains $n$ space-separated integers $a_1, a_2, \\dots, a_n$ ($-10^9 \\le a_i \\le 10^9$).

### Output Specification
Print the $n$ elements in reverse order, separated by a space.

### Sample Input
```
5
1 2 3 4 5
```

### Sample Output
```
5 4 3 2 1
```
""",
        "tests": [
            ("5\n1 2 3 4 5\n", "5 4 3 2 1\n"),
            ("1\n42\n", "42\n"),
            ("4\n-10 20 -30 40\n", "40 -30 20 -10\n"),
            ("6\n7 7 7 8 8 9\n", "9 8 8 7 7 7\n"),
            ("7\n10 20 30 40 50 60 70\n", "70 60 50 40 30 20 10\n"),
        ],
    },
    {
        "code": "cpp07_palindrome",
        "name": "Palindrome String",
        "type": "Strings",
        "group": "Beginner",
        "points": 100,
        "time_limit": 1.0,
        "memory_limit": 262144,
        "description": """## Problem Statement
A palindrome is a string that reads the same forwards and backwards.
Given a non-empty string $s$ consisting of lowercase English letters, determine if it is a palindrome.

### Input Specification
A single line containing the string $s$ ($1 \\le |s| \\le 10^5$).

### Output Specification
Print `YES` if $s$ is a palindrome, or `NO` otherwise.

### Sample Input 1
```
radar
```
### Sample Output 1
```
YES
```

### Sample Input 2
```
dutoj
```
### Sample Output 2
```
NO
```
""",
        "tests": [
            ("radar\n", "YES\n"),
            ("dutoj\n", "NO\n"),
            ("a\n", "YES\n"),
            ("abccba\n", "YES\n"),
            ("abcdecba\n", "NO\n"),
        ],
    },
    {
        "code": "cpp08_gcd_lcm",
        "name": "Greatest Common Divisor and LCM",
        "type": "Mathematics",
        "group": "Beginner",
        "points": 100,
        "time_limit": 1.0,
        "memory_limit": 262144,
        "description": """## Problem Statement
Given two positive integers $a$ and $b$, calculate their Greatest Common Divisor ($\\gcd(a, b)$) and Least Common Multiple ($\\text{lcm}(a, b)$).

### Input Specification
A single line containing two positive integers $a$ and $b$ ($1 \\le a, b \\le 10^9$).

### Output Specification
Print $\\gcd(a, b)$ and $\\text{lcm}(a, b)$ on a single line, separated by a space.

### Sample Input
```
12 18
```

### Sample Output
```
6 36
```
""",
        "tests": [
            ("12 18\n", "6 36\n"),
            ("7 13\n", "1 91\n"),
            ("100 100\n", "100 100\n"),
            ("1 1000000\n", "1 1000000\n"),
            ("48 180\n", "12 720\n"),
        ],
    },
    {
        "code": "cpp09_linear_search",
        "name": "Linear Search in Array",
        "type": "Sorting",
        "group": "Beginner",
        "points": 100,
        "time_limit": 1.0,
        "memory_limit": 262144,
        "description": """## Problem Statement
Given an array of $n$ integers and a target number $x$, find the 1-based index of the first occurrence of $x$ in the array. If $x$ is not present, output `-1`.

### Input Specification
* The first line contains two integers $n$ and $x$ ($1 \\le n \\le 10^5, -10^9 \\le x \\le 10^9$).
* The second line contains $n$ space-separated integers $a_1, a_2, \\dots, a_n$.

### Output Specification
Print the 1-based index of the first occurrence of $x$, or `-1` if $x$ is not in the array.

### Sample Input 1
```
5 7
2 4 7 8 7
```
### Sample Output 1
```
3
```

### Sample Input 2
```
4 10
1 2 3 4
```
### Sample Output 2
```
-1
```
""",
        "tests": [
            ("5 7\n2 4 7 8 7\n", "3\n"),
            ("4 10\n1 2 3 4\n", "-1\n"),
            ("1 5\n5\n", "1\n"),
            ("6 -3\n0 1 2 -3 4 5\n", "4\n"),
            ("5 9\n9 9 9 9 9\n", "1\n"),
        ],
    },
    {
        "code": "cpp10_fibonacci",
        "name": "Fibonacci Number",
        "type": "Dynamic Prog.",
        "group": "Beginner",
        "points": 100,
        "time_limit": 1.0,
        "memory_limit": 262144,
        "description": """## Problem Statement
The Fibonacci sequence is defined as follows:
* $F(0) = 0$
* $F(1) = 1$
* $F(n) = F(n-1) + F(n-2)$ for $n \\ge 2$.

Given an integer $n$, compute the $n$-th Fibonacci number modulo $10^9 + 7$.

### Input Specification
A single line containing an integer $n$ ($0 \\le n \\le 10^6$).

### Output Specification
Print $F(n) \\pmod{10^9 + 7}$.

### Sample Input 1
```
6
```
### Sample Output 1
```
8
```

### Sample Input 2
```
10
```
### Sample Output 2
```
55
```
""",
        "tests": [
            ("0\n", "0\n"),
            ("1\n", "1\n"),
            ("6\n", "8\n"),
            ("10\n", "55\n"),
            ("30\n", "832040\n"),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed 10 basic C++ problems with complete English statements and real test cases"

    def handle(self, *args, **options):
        data_root = getattr(settings, "DMOJ_PROBLEM_DATA_ROOT", "/problems")
        os.makedirs(data_root, exist_ok=True)
        languages = list(Language.objects.all())

        self.stdout.write(self.style.NOTICE("Creating 10 basic C++ problems..."))

        for pdata in PROBLEMS:
            code = pdata["code"]
            name = pdata["name"]
            ptype, _ = ProblemType.objects.get_or_create(name=pdata["type"])
            group, _ = ProblemGroup.objects.get_or_create(name=pdata["group"])

            problem, created = Problem.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": pdata["description"],
                    "time_limit": pdata["time_limit"],
                    "memory_limit": pdata["memory_limit"],
                    "points": pdata["points"],
                    "partial": True,
                    "group": group,
                    "is_public": True,
                    "is_manually_managed": False,
                },
            )
            problem.types.add(ptype)
            if languages:
                problem.allowed_languages.set(languages)
            problem.save()

            # Create testcase files on disk
            prob_dir = os.path.join(data_root, code)
            os.makedirs(prob_dir, exist_ok=True)
            zip_name = f"{code}.zip"
            zip_path = os.path.join(prob_dir, zip_name)
            test_cases_yaml = []

            with zipfile.ZipFile(zip_path, "w") as zf:
                for idx, (inp, out) in enumerate(pdata["tests"], start=1):
                    in_name = f"{idx}.in"
                    out_name = f"{idx}.out"
                    zf.writestr(in_name, inp)
                    zf.writestr(out_name, out)
                    test_cases_yaml.append(
                        {
                            "in": in_name,
                            "out": out_name,
                            "points": 20,
                        }
                    )

            init_yml = {
                "archive": zip_name,
                "test_cases": test_cases_yaml,
            }
            with open(os.path.join(prob_dir, "init.yml"), "w") as f:
                yaml.dump(init_yml, f)

            pd, _ = ProblemData.objects.get_or_create(
                problem=problem,
                defaults={"checker": "standard"},
            )
            pd.zipfile.name = f"{code}/{zip_name}"
            pd.save()

            # Refresh ProblemTestCase database rows
            ProblemTestCase.objects.filter(dataset=problem).delete()
            for idx in range(1, len(pdata["tests"]) + 1):
                ProblemTestCase.objects.create(
                    dataset=problem,
                    order=idx,
                    type="C",
                    input_file=f"{idx}.in",
                    output_file=f"{idx}.out",
                    points=20,
                    is_pretest=False,
                )

            self.stdout.write(
                self.style.SUCCESS(f"  ✓ [{code}] {name} ({len(pdata['tests'])} tests)")
            )

        self.stdout.write(
            self.style.SUCCESS("\nSuccessfully seeded 10 real C++ problems!")
        )
