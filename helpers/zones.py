from enum import Enum

class CarbonAwareRegion(Enum):
    # EUROPE
    STOCKHOLM = {"aws": "eu-north-1", "em_zone": "SE-SE3"}
    FRANKFURT = {"aws": "eu-central-1", "em_zone": "DE"}
    IRELAND = {"aws": "eu-west-1", "em_zone": "IE"}
    LONDON = {"aws": "eu-west-2", "em_zone": "GB"}
    PARIS = {"aws": "eu-west-3", "em_zone": "FR"}
    MILAN = {"aws": "eu-south-1", "em_zone": "IT-NO"}
    SPAIN = {"aws": "eu-south-2", "em_zone": "ES"}
    ZURICH = {"aws": "eu-central-2", "em_zone": "CH"}

    # NORTH AMERICA
    QUEBEC = {"aws": "ca-central-1", "em_zone": "CA-QC"}
    CALGARY = {"aws": "ca-west-1", "em_zone": "CA-AB"}
    VIRGINIA = {"aws": "us-east-1", "em_zone": "US-MIDW-PJM"}
    OHIO = {"aws": "us-east-2", "em_zone": "US-MIDW-PJM"}
    OREGON = {"aws": "us-west-2", "em_zone": "US-NW-PACW"}
    CALIFORNIA = {"aws": "us-west-1", "em_zone": "US-CAL-CISO"}

    # ASIA PACIFIC
    TOKYO = {"aws": "ap-northeast-1", "em_zone": "JP-TK"}
    OSAKA = {"aws": "ap-northeast-3", "em_zone": "JP-KN"}
    SYDNEY = {"aws": "ap-southeast-2", "em_zone": "AU-NSW"}
    MUMBAI = {"aws": "ap-south-1", "em_zone": "IN-WE"}

    @property
    def aws_id(self):
        #aws zone
        return self.value["aws"]

    @property
    def em_id(self):
        #electricy maps zone
        return self.value["em_zone"]

    @classmethod
    def from_em_zone(cls, zone_id):
        for region in cls:
            if region.em_id == zone_id:
                return region
        return None