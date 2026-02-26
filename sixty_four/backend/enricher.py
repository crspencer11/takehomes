import pandas as pd
import requests
import time
from typing import Optional

base_url = "https://api.sixtyfour.ai/"

class Workflow:
    def __init__(self, api_key: Optional[str], file: str):
        self.api_key = api_key
        self.df = pd.read_csv(file)

    @staticmethod
    def generate_struct_from_df(df: pd.DataFrame) -> dict:
        return {col: f"The individual's {col.replace('_', ' ')}" for col in df.columns} # build struct with df cols

    def enrich_data_async(self, struct: Optional[dict], research_plan: Optional[str]) -> Optional[str]:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        lead_info = self.df.to_dict(orient="records")
        if struct is None:
            struct = self.generate_struct_from_df(self.df)
        data = {
            "lead_info": lead_info,
            "struct": struct,
        }
        if research_plan:
            data["research_plan"] = research_plan
        enrich_url = base_url + "enrich-lead-async"
        response = requests.post(enrich_url, json=data, headers=headers)
        if response.status_code < 300:
            return response.json().get("task_id")
        return None

    def poll_job_status(self, task_id: str, poll_interval: int = 10, timeout: int = 900):
        headers = {"x-api-key": self.api_key}
        status_url = base_url + f"job-status/{task_id}"
        start = time.time()
        while time.time() - start < timeout:
            response = requests.get(status_url, headers=headers)
            if response.status_code < 300:
                result = response.json()
                if result.get("status") == "completed":
                    # Update self.df with the enriched data if available
                    if "structured_data" in result["result"]:
                        self.df = pd.DataFrame([result["result"]["structured_data"]])
                    return result.get("result", result)
                elif result.get("status") == "failed":
                    return {"error": "Job failed"}
            time.sleep(poll_interval)
        return {"error": "Polling timed out"}

    def filter(self, filter_exprs: list):
        if not filter_exprs:
            return self
        mask = pd.Series([True] * len(self.df))
        for expr in filter_exprs:
            if callable(expr):
                mask &= expr(self.df)
            elif isinstance(expr, str):
                mask &= eval(expr, {"df": self.df, "pd": pd})
            else:
                raise ValueError("filter_expr must be a callable or a string expression.")
        self.df = self.df[mask]
        return self

    def find_email(self, email: str, research_plan: Optional[str]) -> dict:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        lead_info = self.df.to_dict(orient="records")
        data = {
            "lead_info": lead_info,
            "email": email,
        }
        if research_plan:
            data["research_plan"] = research_plan
        find_email_url = base_url + "find-email"
        response = requests.post(find_email_url, json=data, headers=headers)
        if response.status_code < 300:
            return response.json()
        if 400 <= response.status_code < 500:
            return {"error": "Client Error"}
        if 500 <= response.status_code:
            return {"error": "Internal Server Error"}
        return {"error": "Unknown Error"}

    def save_csv(self, file_path: str):
        self.df.to_csv(file_path, index=False)
        return self

    def add_is_american_education(self, education_col: str = "educational_background"):
        def check_american_edu(val):
            if pd.isnull(val):
                return False
            return "United States" in str(val) or "USA" in str(val)
        self.df["is_american_education"] = self.df[education_col].apply(check_american_edu)
        return self
