import json
import os
import sys
from datetime import datetime, timezone, timedelta
from algorithms import spatio_temporal_hybrid

PLAN_FILE = "plan.json"


def load_config(config_path="user_config.json"):
    with open(config_path, "r") as f:
        return json.load(f)


def write_github_output(should_run, region, machine_type, prov_model, workload):
    """Writes the scheduling results directly to GitHub Actions output environment."""
    if not os.environ.get('GITHUB_OUTPUT'):
        return
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write(f"should_run={str(should_run).lower()}\n")
        if region:
            f.write(f"region={region}\n")
        f.write(f"machine_type={machine_type}\n")
        f.write(f"provisioning_model={prov_model}\n")
        f.write(f"workload={workload}\n")


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

    # Wenn die geplante Zeit erreicht ist (oder weniger als 5 Minuten entfernt)
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

    # HIER SIND DIE GLOBALEN CALLS DIREKT UNTEREINANDER
    active_profile = config.get("active_profile")
    active_workload = config.get("active_workload", "short")  # Holt sich den Workload von der Root-Ebene

    params = config.get("profiles", {}).get(active_profile, {})
    batching_enabled = params.get("enable_batching", True)

    print(f"--- ACTIVE PROFILE: {active_profile.upper()} ---")
    print(f"--- GLOBAL WORKLOAD: {active_workload.upper()} ---")

    # 1. IMMEDIATE-Strategien (Latency / Cost)
    if params.get("strategy") == "immediate":
        if batching_enabled:
            plan_result = check_existing_plan(params["machine_type"], params["provisioning_model"])
            if plan_result:
                write_github_output(plan_result["should_run"], params["region"], params["machine_type"],
                                    params["provisioning_model"], active_workload)
                return

            delay_minutes = params.get("batch_window_minutes", 15)
            target_time = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)

            print(f"[Batching] Initializing new batch for {active_profile}. Waiting {delay_minutes} minutes.",
                  file=sys.stderr)
            with open(PLAN_FILE, "w") as f:
                json.dump({"planned_time": target_time.isoformat(), "region": params["region"], "batch_count": 1}, f)

            write_github_output(False, params["region"], params["machine_type"], params["provisioning_model"],
                                active_workload)
            return
        else:
            write_github_output(True, params["region"], params["machine_type"], params["provisioning_model"],
                                active_workload)
            return

    # 2. CARBON-Strategie (Spatio-Temporal)
    if batching_enabled:
        plan_result = check_existing_plan(params["machine_type"], params["provisioning_model"])
        if plan_result:
            write_github_output(plan_result["should_run"], plan_result["region"], params["machine_type"],
                                params["provisioning_model"], active_workload)
            return

    result = spatio_temporal_hybrid.evaluate(params)

    if batching_enabled and not result.get("should_run") and result.get("planned_time"):
        with open(PLAN_FILE, "w") as f:
            json.dump({"planned_time": result["planned_time"], "region": result["region"], "batch_count": 1}, f)

    write_github_output(result.get("should_run"), result.get("region"), params["machine_type"],
                        params["provisioning_model"], active_workload)


if __name__ == "__main__":
    main()