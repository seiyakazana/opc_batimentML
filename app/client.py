import requests

URL = "http://15.237.183.95:3000/predict"
# URL = "http://localhost:3000/predict"

payload = {
    "rows": [
        {
            "BuildingType": "NonResidential",
            "NumberofBuildings": 1,
            "NumberofFloors": 12,
            "PropertyGFATotal": 88434,
            "Neighborhood_EAST": 0,
            "source_of_energy": 3,
            "Building_Age": 100,

            "PropertyUseDetails": {
                "Lodging": 88434,
                "Retail": 0,
                "Office": 0,
            },
        }
    ]
}

r = requests.post(URL, json={"request": payload}, timeout=30)
print(r.status_code)
print(r.text)
