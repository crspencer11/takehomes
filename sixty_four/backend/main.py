import os
from enricher import Workflow

API_KEY = os.getenv("API_KEY")
csv_file = "backend/sixty-four-sample-data.csv"

def main():
    workflow = Workflow(api_key=API_KEY, file=csv_file)
    filters = [
        f"df['company'].str.contains('Ariglad Inc')",
        lambda df: df['company_location'].str.lower().str.contains('united states')
    ]
    workflow.filter(filters)

    task_id = workflow.enrich_data_async()
    if task_id:
        result = workflow.poll_job_status(task_id)
        if result:
            # workflow.df is updated in poll_job_status if enrichment is successful
            workflow.save_csv("backend/output.csv")
            print(workflow.df.head())
    else:
        print("Failed to start async enrichment job.")

if __name__ == "__main__":
    main()
