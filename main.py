import json
import os
import sys
from datetime import datetime, timezone, timedelta
from algorithms import spatio_temporal_hybrid

PLAN_FILE = "plan.json"


def load_config(config_path="user_config.json"):
    with open(config_path, "r") as f:
        return json.load(f)


def write_github_output(should_run, region, machine_type, prov_model, workload, runner_name):
    """Writes the scheduling results directly to GitHub Actions output environment."""
    if not os.environ.get('GITHUB_OUTPUT'):
        return
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write(f"should_run={str(should_run).lower()}\n")
        f.write(f"region={region if region else ''}\n")  # Verhindert leere Variablen-Crashes in Terraform
        f.write(f"machine_type={machine_type}\n")
        f.write(f"provisioning_model={prov_model}\n")
        f.write(f"workload={workload}\n")
        f.write(f"runner_name={runner_name}\n")


def check_existing_plan(machine_type, prov_model):
    """Checks if a plan already exists and evaluates if it's time to run."""
    if not os.path.exists(PLAN_FILE):
        return None

    with open(PLAN_FILE, "r") as f:
        plan = json.load(f)

    plan["batch_count"] = plan.get("batch_count", 1) + 1

    target_time = datetime.fromisoformat(plan["planned_time"])
    now = datetime.now(timezone.utc)

    # Differenz in Minuten berechnen
    time_diff_minutes = (target_time - now).total_seconds() / 60

    if time_diff_minutes <= 5:
        print(f"[Batching] It is time! Executing consolidated run ({plan['batch_count']} commits).", file=sys.stderr)
        os.remove(PLAN_FILE)
        return {"should_run": True, "region": plan["region"]}
    else:
        with open(PLAN_FILE, "w") as f:
            json.dump(plan, f)
        print(
            f"[Batching] Delayed. Current queue: {plan['batch_count']} commits. Time left: {time_diff_minutes:.0f} min.",
            file=sys.stderr)
        return {"should_run": False, "region": None}


def main():
    config = load_config()

    active_profile = config.get("active_profile")
    active_workload = config.get("active_workload", "short")

    params = config.get("profiles", {}).get(active_profile, {})
    runner_name = params.get("runner_name", "green-thesis-runner")

    print(f"--- ACTIVE PROFILE: {active_profile.upper()} ---")
    print(f"--- GLOBAL WORKLOAD: {active_workload.upper()} ---")

    # 1. IMMEDIATE-Strategien (Latency / Cost)
    if params.get("strategy") == "immediate":
        fixed_region = params.get("region")

        batching_enabled_immediate = params.get("enable_batching", False)

        if batching_enabled_immediate:
            plan_result = check_existing_plan(params["machine_type"], params["provisioning_model"])
            if plan_result:
                # FIXED: Wir nutzen fixed_region statt plan_result["region"], falls noch Fragmente im Cache lagen
                write_github_output(plan_result["should_run"], fixed_region, params["machine_type"],
                                    params["provisioning_model"], active_workload, runner_name)
                return

            delay_minutes = params.get("batch_window_minutes", 15)
            target_time = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)

            print(f"[Batching] Initializing new batch for {active_profile}. Waiting {delay_minutes} minutes.",
                  file=sys.stderr)
            with open(PLAN_FILE, "w") as f:
                json.dump({"planned_time": target_time.isoformat(), "region": fixed_region, "batch_count": 1}, f)

            write_github_output(False, fixed_region, params["machine_type"], params["provisioning_model"],
                                active_workload, runner_name)
            return
        else:
            write_github_output(True, fixed_region, params["machine_type"], params["provisioning_model"],
                                active_workload, runner_name)
            return

    # 2. CARBON-Strategie (Spatio-Temporal)
    batching_enabled_carbon = params.get("enable_batching", True)  # Für Carbon bleibt Default True

    if batching_enabled_carbon:
        plan_result = check_existing_plan(params["machine_type"], params["provisioning_model"])
        if plan_result:
            write_github_output(plan_result["should_run"], plan_result["region"], params["machine_type"],
                                params["provisioning_model"], active_workload, runner_name)
            return

    result = spatio_temporal_hybrid.evaluate(params)

    if batching_enabled_carbon and not result.get("should_run") and result.get("planned_time"):
        with open(PLAN_FILE, "w") as f:
            json.dump({"planned_time": result["planned_time"], "region": result["region"], "batch_count": 1}, f)

    write_github_output(result.get("should_run"), result.get("region"), params["machine_type"],
                        params["provisioning_model"], active_workload, runner_name)


if __name__ == "__main__":
    main()