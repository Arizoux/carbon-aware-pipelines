import json
import os
import sys
from helpers.zones import CarbonAwareRegion

# Import your algorithm modules
from algorithms import predictive_window, threshold_greedy, spatio_temporal_hybrid


def load_config(config_path="user_config.json"):
    """Loads the user configuration from the root directory."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {config_path} not found.", file=sys.stderr)
        sys.exit(1)


def write_github_output(should_run, region):
    """Writes results to the GITHUB_OUTPUT environment file."""
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"should_run={str(should_run).lower()}\n")
            f.write(f"region={region if region else ''}\n")
    else:
        # Local testing fallback
        print("\n--- Local Execution Result ---")
        print(f"Should Run: {should_run}")
        print(f"AWS Region: {region}")
        print("------------------------------")


def main():
    # 1. Load User Configuration
    config = load_config()
    active_algo = config.get("active_algorithm")
    params = config.get("parameters", {}).get(active_algo, {})
    
    print(f"Starting Scheduler...")
    print(f"Algorithm: {active_algo}")
    print(f"Parameters: {params}")

    # 2. Strategy Router: Execute the chosen algorithm
    # Each evaluate() function returns {"should_run": bool, "region": str or None}

    try:
        if active_algo == "threshold_greedy":
            result = threshold_greedy.evaluate(params)

        elif active_algo == "predictive_window":
            result = predictive_window.evaluate(params)

        elif active_algo == "spatio_temporal_hybrid":
            result = spatio_temporal_hybrid.evaluate(params)

        else:
            print(f"Error: Algorithm '{active_algo}' not recognized.", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Execution Error: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Output the result to GitHub Actions

    #write_github_output(result["should_run"], result["region"])
    print(result)

if __name__ == "__main__":
    main()