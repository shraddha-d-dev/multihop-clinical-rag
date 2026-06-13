import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
MAX_STUDIES = int(os.getenv("MAX_STUDIES"))


#target conditions:
#Rheumatoid Arthritis + Non-Small Cell Lung Cancer + Type 2 Diabetes + Heart Failure

def fetch_trial_data(condition: str, max_studies: int) -> dict:

    params = {
        "query.cond": condition,
        "filter.overallStatus": "COMPLETED",
        'pageSize': 100,
        'fields': (
            "protocolSection.identificationModule.nctId,"
            "protocolSection.identificationModule.briefTitle,"
            "protocolSection.conditionsModule.conditions,"
            "protocolSection.designModule.phases,"
            "protocolSection.armsInterventionsModule.interventions,"
            "protocolSection.outcomesModule.primaryOutcomes,"
            "protocolSection.designModule.enrollmentInfo,"
            "protocolSection.statusModule.startDateStruct,"
            "protocolSection.statusModule.completionDateStruct,"
            "protocolSection.sponsorCollaboratorsModule.leadSponsor,"
            "protocolSection.descriptionModule.briefSummary,"
            "protocolSection.descriptionModule.detailedDescription,"
            "protocolSection.eligibilityModule.eligibilityCriteria,"
            "resultsSection"
        )
    }

    studies = []
    next_page_token = None
    num_requests = 0
    
    while len(studies) < max_studies:
        if next_page_token:
            params['pageToken'] = next_page_token

        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()
    
        studies.extend(data.get('studies', []))
        next_page_token = data.get('nextPageToken')

        num_requests += 1
        print(f"Request no. {num_requests} completed.")
        if not next_page_token:
            break

    return studies

if __name__ == '__main__':

    all_studies = []
    max_studies = MAX_STUDIES # 585919 
    # Target conditions: Rheumatoid Arthritis, Non-Small Cell Lung Cancer, Type 2 Diabetes, Heart Failure
    conditions = ["Rheumatoid Arthritis", "Non-Small Cell Lung Cancer", "Type 2 Diabetes", "Heart Failure"]

    for condition in conditions:
        print(f"Fetching data for '{condition}' condition...")
        studies = fetch_trial_data(condition, max_studies)
        all_studies.extend(studies)

    with open('trial_data.json', 'w') as f:
        json.dump(all_studies, f, indent=4)

    print('Data fetching completed. Number of studies fetched: {}'.format(len(all_studies))) 
    # 16803