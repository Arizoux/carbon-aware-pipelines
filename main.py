import json
import os
import sys
from datetime import datetime, timezone

from algorithms import predictive_window, threshold_greedy, spatio_temporal_hybrid

PLAN_FILE = "plan.json"


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
        print(f"GCP Region: {region}")
        print("------------------------------")


def check_existing_plan():
    """Checks if a plan already exists and evaluates if it's time to run."""
    if not os.path.exists(PLAN_FILE):
        return None

    try:
        with open(PLAN_FILE, "r") as f:
            plan = json.load(f)

        target_time = datetime.fromisoformat(plan["planned_time"])
        now = datetime.now(timezone.utc)

        # Calculate time difference in hours
        time_diff_hours = (target_time - now).total_seconds() / 3600

        # If the target time is within the next 15 minutes (or in the past)
        if time_diff_hours <= 0.25:
            print(f"[State] It is time! Executing planned run in {plan['region']}.", file=sys.stderr)
            os.remove(PLAN_FILE)  # remove the plan so it doesn't run twice
            return {"should_run": True, "region": plan["region"]}
        else:
            print(f"[State] Waiting... Scheduled for {target_time.strftime('%H:%M')} UTC (in {time_diff_hours:.2f}h).",
                  file=sys.stderr)
            return {"should_run": False, "region": None}

    except Exception as e:
        print(f"Error reading plan: {e}. Deleting corrupted plan.", file=sys.stderr)
        os.remove(PLAN_FILE)
        return None


def save_plan(planned_time, region):
    """Saves the scheduled execution to a file."""
    if not planned_time or not region:
        return

    plan = {
        "planned_time": planned_time,
        "region": region
    }
    with open(PLAN_FILE, "w") as f:
        json.dump(plan, f)
    print(f"[State] Saved future execution plan for {planned_time} in {region}.", file=sys.stderr)


def main():
    plan_result = check_existing_plan()
    if plan_result:
        write_github_output(plan_result["should_run"], plan_result["region"])
        print(plan_result)
        return

    config = load_config()
    active_algo = config.get("active_algorithm")
    params = config.get("parameters", {}).get(active_algo, {})

    print(f"Starting Scheduler...")
    print(f"Algorithm: {active_algo}")

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

    if result.get("should_run") is False and result.get("planned_time"):
        save_plan(result["planned_time"], result["region"])

    # Output the result to GitHub Actions
    write_github_output(result.get("should_run", False), result.get("region"))
    print(result)


if __name__ == "__main__":
    main()