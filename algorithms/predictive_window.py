import os
import sys
import requests
from datetime import datetime, timezone, timedelta
from helpers.zones import CarbonAwareRegion


def get_forecast_for_zone(zone_id):
    """fetches forecast data from Electricity Maps API."""
    api_key = os.environ.get("ELECTRICITY_MAPS_API_KEY")
    if not api_key:
        raise ValueError("ELECTRICITY_MAPS_API_KEY is not set in environment.")

    url = f"https://api.electricitymap.org/v3/carbon-intensity/forecast?zone={zone_id}"
    headers = {"auth-token": api_key}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print(response.json())
    return response.json().get("forecast", [])


def evaluate(params):
    """
    Uses the params passed from main.py to find the optimal
    time slot for a contiguous workload.
    """
    # 1. Access data passed from main.py
    # These keys must match the user_config.json exactly
    region_name = params.get("target_region")
    build_duration = params.get("run_duration")
    forecast_window = params.get("forecast_window_hours")

    if not all([region_name, build_duration, forecast_window]):
        print(f"Error: Missing required parameters for Predictive Window. Got: {params}", file=sys.stderr)
        return {"should_run": False, "region": None}

    # 2. Resolve the Enum for AWS/EM IDs
    try:
        region_enum = CarbonAwareRegion[region_name]
    except KeyError:
        print(f"Error: {region_name} not found in CarbonAwareRegion enum.", file=sys.stderr)
        return {"should_run": False, "region": None}

    try:
        # 3. Fetch Data
        forecast_data = get_forecast_for_zone(region_enum.em_id)

        now = datetime.now(timezone.utc)
        limit_time = now + timedelta(hours=forecast_window)

        # Filter forecast for the search window
        relevant_points = [
            p for p in forecast_data
            if now <= datetime.fromisoformat(p["datetime"].replace('Z', '+00:00')) <= limit_time
        ]

        # Calculate K (number of 15-min intervals in the build)
        # 2 hours = 8 points
        k_points = int((build_duration * 60) / 15)

        if len(relevant_points) < k_points:
            print(f"Error: Not enough data points ({len(relevant_points)}) for {build_duration}h build.",
                  file=sys.stderr)
            return {"should_run": False, "region": None}

        # 4. Sliding Window Implementation
        best_avg_ci = float('inf')
        best_start_time = None

        for i in range(len(relevant_points) - k_points + 1):
            window = relevant_points[i: i + k_points]
            avg_ci = sum(p["carbonIntensity"] for p in window) / k_points

            if avg_ci < best_avg_ci:
                best_avg_ci = avg_ci
                best_start_time = datetime.fromisoformat(window[0]["datetime"].replace('Z', '+00:00'))

        # 5. Final Decision
        time_until_start = (best_start_time - now).total_seconds() / 3600

        print(f"[Predictive Window] Target: {region_name} | Best Start: {best_start_time} | Avg CI: {best_avg_ci:.1f}",
              file=sys.stderr)

        # If best start is within 15 mins (0.25h), run it!
        if time_until_start <= 0.25:
            return {
                "should_run": True,
                "region": region_enum.aws_id
            }
        else:
            print(f"Optimal slot is {time_until_start:.1f}h away. Waiting...", file=sys.stderr)
            return {"should_run": False, "region": None}

    except Exception as e:
        print(f"Algorithm Error: {e}", file=sys.stderr)
        return {"should_run": False, "region": None}