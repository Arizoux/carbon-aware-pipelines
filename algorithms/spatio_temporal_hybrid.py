import os
from dotenv import load_dotenv
import sys
import requests
import time
from datetime import datetime, timezone, timedelta
from helpers.zones import CarbonAwareRegion

load_dotenv()

ELECTRICITY_MAPS_API_KEY = os.getenv("ELECTRICITY_MAPS_API_KEY")


def get_forecast_for_zone(zone_id):
    """Fetches the 15-minute granularity forecast from Electricity Maps."""
    api_key = os.environ.get("ELECTRICITY_MAPS_API_KEY")
    url = f"https://api.electricitymap.org/v3/carbon-intensity/forecast?zone={zone_id}&temporalGranularity=15_minutes"
    headers = {"auth-token": api_key}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get("forecast", [])
    except Exception as e:
        print(f"Warning: API call failed for {zone_id}: {e}", file=sys.stderr)
        return []


def get_filtered_regions(allowed_param):
    """
    Parses the allowed_regions parameter to return a list of Enum members.
    Supports keywords: 'all', 'europe', 'america', 'asia' or a specific list.
    """
    groups = {
        "europe": ["STOCKHOLM", "FRANKFURT", "IRELAND", "LONDON", "PARIS", "MILAN", "SPAIN", "ZURICH"],
        "america": ["QUEBEC", "CALGARY", "VIRGINIA", "OHIO", "OREGON", "CALIFORNIA"],
        "asia": ["TOKYO", "OSAKA", "SYDNEY", "MUMBAI"]
    }

    selected_names = []

    # Case 1: String Keyword ("all", "europe", "america" or "asia)
    if isinstance(allowed_param, str):
        choice = allowed_param.lower()
        if choice == "all":
            return list(CarbonAwareRegion)
        elif choice in groups:
            selected_names = groups[choice]
        else:
            print(f"Warning: Unknown region group '{choice}'. Falling back to ALL.", file=sys.stderr)
            return list(CarbonAwareRegion)

    # Case 2: Specific List (e.g., ["STOCKHOLM", "QUEBEC"])
    elif isinstance(allowed_param, list):
        selected_names = allowed_param

    else:
        return list(CarbonAwareRegion)

    members = []
    for name in selected_names:
        try:
            members.append(CarbonAwareRegion[name])
        except KeyError:
            print(f"Warning: {name} is not defined in CarbonAwareRegion Enum.", file=sys.stderr)

    return members


def evaluate(params):
    """
    Spatio-Temporal Hybrid Strategy:
    Checks all selected regions and finds the best 15-minute window
    within the forecast horizon.
    """
    # 1. Extract Config
    run_duration = params.get("run_duration")
    forecase_window_hours = params.get("forecast_window_hours")
    allowed_regions = params.get("allowed_regions", "all")

    # 2. Get target regions based on config
    target_regions = get_filtered_regions(allowed_regions)

    now = datetime.now(timezone.utc)
    limit_time = now + timedelta(hours=forecase_window_hours)
    k_points = int((run_duration * 60) / 15)

    global_best = {
        "avg_ci": float('inf'),
        "start_time": None,
        "region": None
    }

    print(f"[Hybrid] Evaluating {len(target_regions)} regions (Scope: {allowed_regions})", file=sys.stderr)

    # 3. Iterate through every target region
    for region in target_regions:
        print(f"current region: {region.name}", file=sys.stderr)
        forecast_data = get_forecast_for_zone(region.em_id)

        # Filter data points within our search horizon
        relevant_points = [
            p for p in forecast_data
            if now <= datetime.fromisoformat(p["datetime"].replace('Z', '+00:00')) <= limit_time
        ]

        if len(relevant_points) < k_points:
            continue

        # 4. Sliding Window calculation for this specific region
        for i in range(len(relevant_points) - k_points + 1):
            window = relevant_points[i: i + k_points]
            avg_ci = sum(p["carbonIntensity"] for p in window) / k_points

            # Update global minimum if this window is cleaner
            if avg_ci < global_best["avg_ci"]:
                global_best = {
                    "avg_ci": avg_ci,
                    "start_time": datetime.fromisoformat(window[0]["datetime"].replace('Z', '+00:00')),
                    "region": region
                }

    # 5. Result Determination
    if global_best["region"] is None:
        print("Error: No forecast data found for selected regions.", file=sys.stderr)
        return {"should_run": False, "region": None}

    best_region = global_best["region"]
    best_start = global_best["start_time"]
    time_until_start = (best_start - now).total_seconds() / 3600

    print(f"--- Global Winner ---", file=sys.stderr)
    print(f"Region: {best_region.name} ({best_region.aws_id})", file=sys.stderr)
    print(f"Optimal Start: {best_start} UTC (in {time_until_start:.2f}h)", file=sys.stderr)
    print(f"Avg CI: {global_best['avg_ci']:.1f} gCO2eq/kWh", file=sys.stderr)

    # 6. Return Decision
    # Trigger if we are within the 15-minute start window
    if time_until_start <= 0.25:
        return {
            "should_run": True,
            "region": best_region.aws_id
        }
    else:
        print(f"Waiting for more optimal conditions in {best_region.name}...", file=sys.stderr)
        return {"should_run": False, "region": None}