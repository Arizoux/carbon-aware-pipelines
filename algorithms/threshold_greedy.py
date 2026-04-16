import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

ELECTRICITY_MAPS_API_KEY = os.getenv("ELECTRICITY_MAPS_API_KEY")


def get_electricity_maps(zone):
    url = f"https://api.electricitymap.org/v3/carbon-intensity/latest?zone={zone}"
    headers = {"auth-token": ELECTRICITY_MAPS_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["carbonIntensity"]


def evaluate(params):
    region_name = params.get("target_region")
    threshold_GCO2_KWH = params.get("threshold_gco2_kwh")

    if not all([region_name, threshold_GCO2_KWH]):
        print(f"Error: Missing required parameters for Predictive Window. Got: {params}", file=sys.stderr)
        return {"should_run": False, "region": None}

    try:
        current_ci = get_electricity_maps(region_name)
        print(f"Current CI in {region_name}: {current_ci} gCO2eq/kWh", file=sys.stderr)

        if current_ci <= threshold_GCO2_KWH:
            print("should_run=true")
            print("region=eu-central-1")
        else:
            print(f"Threshold not met. Waiting...", file=sys.stderr)
            print("should_run=false")

    except Exception as e:
        print(f"Error fetching data: {e}", file=sys.stderr)
        print("should_run=false")
