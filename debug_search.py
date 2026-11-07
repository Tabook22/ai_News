import sys
import os
import traceback

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

print("--- DIAGNOSTIC START ---")

try:
    from duckduckgo_search import DDGS
    print("1. DDGS imported successfully.")
except ImportError:
    print("CRITICAL: duckduckgo_search not installed.")
    sys.exit(1)

print("2. Attempting DDG Search...")
try:
    with DDGS() as ddgs:
        results = ddgs.news("AI", max_results=5)
        print(f"3. Raw Results Type: {type(results)}")
        # It's a generator usually, let's listify it
        results_list = list(results)
        print(f"4. Results Count: {len(results_list)}")
        if results_list:
            print(f"5. Sample: {results_list[0]}")
        else:
            print("5. No results found.")
except Exception:
    print("❌ ERROR during DDG Search:")
    traceback.print_exc()

print("--- DIAGNOSTIC END ---")
