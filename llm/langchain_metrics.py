from langsmith import Client
import os
from datetime import datetime, timedelta


# Check if API key is set from environment variable
print("Current system time:", datetime.now())
# Initialize client (uses LANGSMITH_API_KEY env var)
client = Client(api_key="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")

def get_recent_runs():
    # Get runs from the last hour
    print("Getting recent runs...")
    try:
        recent_runs = list(client.list_runs(
            project_name="default",  # Your LangSmith project
            limit=50,
        ))
        print(f"Found {len(recent_runs)} runs")

        # Get metrics from recent runs
        for run in recent_runs:
            print(f"Run ID: {run.id}")
            print(f"Name: {run.name}")
            print(f"Status: {run.status}")
            print(f"Tokens: {run.total_tokens}")
            print(f"Cost: ${run.total_cost}")
            print(f"Start time: {run.start_time}")
            print(f"End time: {run.end_time}")
            print(f"Duration: {run.end_time - run.start_time}")
            print(f"Input: {run.inputs}")
            print(f"Output: {run.outputs}")
            print(f"Error: {run.error}")
            print(f"Tags: {run.tags}")
            print(f"Metadata: {run.metadata}")
            print(f"Parent Run ID: {run.parent_run_id}")
            print(f"Child Runs: {run.child_runs}")

            # get the run metrics
            run_metrics = client.get_run_metrics(run.id)
            print(f"Run Metrics: {run_metrics}")

            # get the run events
            run_events = client.get_run_events(run.id)
            print(f"Run Events: {run_events}")
            print("---")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_recent_runs()