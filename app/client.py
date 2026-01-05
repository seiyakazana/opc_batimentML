import requests

URL = "http://35.181.173.155:3000/predict"
#URL = "http://localhost:3000/predict"

payload = {
    "rows": [
        {
            "BuildingType": "NonResidential",
            "NumberofBuildings": 1,
            "NumberofFloors": 12,
            "PropertyGFATotal": 884340,
            "Neighborhood_EAST": 1,
            "source_of_energy": 3,
            "Building_Age": 100,
            "ComplianceStatus": "Non-Compliant",
            "Outlier": "Low outlier",

            "PropertyUseDetails": {
                "Lodging": 440000,
                "Retail": 220000,
                "Office": 88000,
            },
        }
    ]
}

r = requests.post(URL, json={"request": payload}, timeout=30)
print(r.status_code)
print(r.text)
