#!/usr/bin/env python3

def hello_world():
    """Print a friendly greeting."""
    print("Hello, World!")
    print("This is a sample Python script.")

def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

if __name__ == "__main__":
    hello_world()
    
    print("Fibonacci sequence:")
    for i in range(10):
        print(f"F({i}) = {calculate_fibonacci(i)}")