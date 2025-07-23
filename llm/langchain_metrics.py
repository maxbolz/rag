from langsmith import Client
import os
import json
from datetime import datetime, timedelta
import csv
import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()


# Check if API key is set from environment variable
print("Current system time:", datetime.now())

class LangchainMetrics:
    def __init__(self):
        self.API_KEY = os.getenv("LANGSMITH_API_KEY")
        # Initialize client (uses LANGSMITH_API_KEY env var)
        self.client = Client(api_key=self.API_KEY)


    def connect_clickhouse(self):
            """Connect to ClickHouse database"""
            try:
                self.clickhouse_client = clickhouse_connect.get_client(
                    host='10.0.100.92',
                    port=8123,
                    username='user',
                    password='default',
                    database='guardian'
                )
                print("Connected to ClickHouse successfully")
                return True
            except Exception as e:
                print(f"Failed to connect to ClickHouse: {e}")
                self.clickhouse_client = None
                return False

    def save_to_clickhouse(self, run):
        # Upload data to ClickHouse table (assumes connection already established)
        table_name = "langchain_metrics"
        
        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id String,
            name String,
            status String,
            total_tokens Int32,
            total_cost Float64,
            start_time DateTime,
            end_time DateTime,
            duration Float64,
            inputs String,
            outputs String,
            error String,
            tags String,
            metadata String,
            parent_run_id String,
            child_runs String
        ) ENGINE = MergeTree()
        ORDER BY id
        """
        # Create table if not exists (simple schema)
        self.clickhouse_client.command(query)

        # Prepare row for insertion
        row = [
            str(run.id),
            str(run.name),
            str(run.status),
            int(run.total_tokens) if run.total_tokens is not None else 0,
            float(run.total_cost) if run.total_cost is not None else 0.0,
            run.start_time,
            run.end_time,
            float((run.end_time - run.start_time).total_seconds()) if run.end_time and run.start_time else 0.0,
            json.dumps(run.inputs),
            json.dumps(run.outputs),
            str(run.error),
            json.dumps(run.tags),
            json.dumps(run.metadata),
            str(run.parent_run_id),
            json.dumps(run.child_runs)
        ]

        self.clickhouse_client.insert(
            table_name,
            [row],  # a list of rows
            column_names=[
                "id", "name", "status", "total_tokens", "total_cost", "start_time", "end_time",
                "duration", "inputs", "outputs", "error", "tags", "metadata", "parent_run_id", "child_runs"
            ]
        )
        print(f"Run {run.id} saved to ClickHouse")

    def get_recent_runs(self):
        # Get runs from the last hour
        print("Getting recent runs...")
        try:
            recent_runs = list(self.client.list_runs(
                project_name="default",  # Your LangSmith project
                limit=1,
            ))
            print(f"Found {len(recent_runs)} runs")

            # Get metrics from recent runs and convert to a json
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
                print("---")


                
            # csv_file = "recent_runs.csv"
            # fieldnames = [
            #     "id", "name", "status", "total_tokens", "total_cost", "start_time", "end_time",
            #     "duration", "inputs", "outputs", "error", "tags", "metadata", "parent_run_id", "child_runs"
            # ]
            # # Check if file exists to write header only once
            # write_header = not os.path.exists(csv_file)
            # with open(csv_file, mode="a", newline="", encoding="utf-8") as f:
            #     writer = csv.DictWriter(f, fieldnames=fieldnames)
            #     if write_header:
            #         writer.writeheader()
            #     writer.writerow({
            #         "id": run.id,
            #         "name": run.name,
            #         "status": run.status,
            #         "total_tokens": run.total_tokens,
            #         "total_cost": run.total_cost,
            #         "start_time": run.start_time,
            #         "end_time": run.end_time,
            #         "duration": (run.end_time - run.start_time) if run.end_time and run.start_time else None,
            #         "inputs": json.dumps(run.inputs),
            #         "outputs": json.dumps(run.outputs),
            #         "error": run.error,
            #         "tags": json.dumps(run.tags),
            #         "metadata": json.dumps(run.metadata),
            #         "parent_run_id": run.parent_run_id,
            #         "child_runs": json.dumps(run.child_runs),
            #     })
            return recent_runs
                
                
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    langchain_metrics = LangchainMetrics()
    langchain_metrics.connect_clickhouse()
    runs = langchain_metrics.get_recent_runs()
    for run in runs:
        langchain_metrics.save_to_clickhouse(run=run)







