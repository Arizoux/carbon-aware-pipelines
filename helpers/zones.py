from enum import Enum

class CarbonAwareRegion(Enum):
    # --- EUROPE ---
    STOCKHOLM = {"gcp": "europe-north1",      "em_zone": "SE-SE3"}
    FRANKFURT = {"gcp": "europe-west3",       "em_zone": "DE"}
    IRELAND   = {"gcp": "europe-west1",       "em_zone": "IE"}
    LONDON    = {"gcp": "europe-west2",       "em_zone": "GB"}
    PARIS     = {"gcp": "europe-west9",       "em_zone": "FR"}
    MILAN     = {"gcp": "europe-west8",       "em_zone": "IT-NO"}
    SPAIN     = {"gcp": "europe-southwest1",  "em_zone": "ES"}
    ZURICH    = {"gcp": "europe-west6",       "em_zone": "CH"}

    # --- NORTH AMERICA ---
    QUEBEC    = {"gcp": "northamerica-northeast1", "em_zone": "CA-QC"}
    CALGARY   = {"gcp": "northamerica-northeast2", "em_zone": "CA-AB"}
    VIRGINIA  = {"gcp": "us-east4",                "em_zone": "US-MIDW-PJM"}
    OHIO      = {"gcp": "us-east5",                "em_zone": "US-MIDW-PJM"}
    OREGON    = {"gcp": "us-west1",                "em_zone": "US-NW-PACW"}
    CALIFORNIA = {"gcp": "us-west2",               "em_zone": "US-CAL-CISO"}

    # --- ASIA PACIFIC ---
    TOKYO     = {"gcp": "asia-northeast1",    "em_zone": "JP-TK"}
    OSAKA     = {"gcp": "asia-northeast2",    "em_zone": "JP-KN"}
    SYDNEY    = {"gcp": "australia-southeast1", "em_zone": "AU-NSW"}
    MUMBAI    = {"gcp": "asia-south1",        "em_zone": "IN-WE"}

    @property
    def gcp_id(self):
        """Returns the GCP region ID (e.g., 'europe-west3')"""
        return self.value["gcp"]

    @property
    def em_id(self):
        """Returns the Electricity Maps zone ID (e.g., 'DE')"""
        return self.value["em_zone"]

    @classmethod
    def from_em_zone(cls, zone_id):
        """Finds the Enum member by its Electricity Maps ID."""
        for region in cls:
            if region.em_id == zone_id:
                return region
        return None