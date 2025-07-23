from langsmith import Client
import os
import csv
from io import StringIO
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from dotenv import load_dotenv
load_dotenv()


class LangChainMetrics:
    def __init__(self, project_name: str = "default"):
        self.api_key = os.getenv("LANGSMITH_API_KEY")
        self.project_name = project_name
        self.client = Client(api_key=self.api_key)
        
    def get_latest_runs(self, limit: int = 50, hours_back: int = 24) -> List[Any]:
        try:
            start_time = datetime.now() - timedelta(hours=hours_back)
            return list(self.client.list_runs(
                project_name=self.project_name,
                start_time=start_time,
                limit=limit
            ))
        except Exception as e:
            print(f"Error getting latest runs: {e}")
            return []
    
    def get_runs_by_id(self, run_ids: List[str]) -> List[Any]:
        runs = []
        for run_id in run_ids:
            try:
                runs.append(self.client.read_run(run_id))
            except Exception as e:
                print(f"Error retrieving run {run_id}: {e}")
        return runs
    
    def get_runs_by_tags(self, tags: List[str], match_all: bool = True, limit: int = 100) -> List[Any]:
        try:
            operator = " and " if match_all else " or "
            filter_str = operator.join([f'has(tags, "{tag}")' for tag in tags])
            
            return list(self.client.list_runs(
                project_name=self.project_name,
                filter=filter_str,
                limit=limit
            ))
        except Exception as e:
            print(f"Error searching runs by tags {tags}: {e}")
            return []
    
    def get_runs_by_start_time(
        self, 
        start_time_gte: datetime, 
        start_time_lte: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Any]:
        try:
            filters = [f'start_time >= "{start_time_gte.isoformat()}"']
            if start_time_lte:
                filters.append(f'start_time <= "{start_time_lte.isoformat()}"')
            
            return list(self.client.list_runs(
                project_name=self.project_name,
                filter=" and ".join(filters),
                limit=limit
            ))
        except Exception as e:
            print(f"Error searching runs by start time: {e}")
            return []

    def pretty_print_metrics(self, runs: List[Any], group_by: str = "parent_id") -> None:
        # Group runs
        grouped_runs = {}
        if group_by == "parent_id":
            for run in runs:
                parent_id = str(run.parent_run_id) if run.parent_run_id else str(run.id)
                if parent_id not in grouped_runs:
                    grouped_runs[parent_id] = []
                grouped_runs[parent_id].append(run)
        elif group_by == "tag":
            for run in runs:
                tags = run.tags if run.tags else ["no_tag"]
                for tag in tags:
                    if tag not in grouped_runs:
                        grouped_runs[tag] = []
                    grouped_runs[tag].append(run)
        
        # CSV format output
        csv_buffer = StringIO()
        
        # Summary CSV
        print("=== SUMMARY CSV ===")
        summary_writer = csv.writer(csv_buffer)
        summary_writer.writerow([
            "group_key", "group_type", "total_runs", "total_cost", "total_tokens", 
            "success_count", "error_count", "success_rate"
        ])
        
        for group_key, group_runs in grouped_runs.items():
            success_count = sum(1 for run in group_runs if run.status == "success")
            summary_writer.writerow([
                group_key,
                group_by,
                len(group_runs),
                sum(float(run.total_cost or 0) for run in group_runs),
                sum(int(run.total_tokens or 0) for run in group_runs),
                success_count,
                len(group_runs) - success_count,
                f"{(success_count / len(group_runs) * 100):.1f}%" if group_runs else "0%"
            ])
        
        #print(csv_buffer.getvalue())
        csv_buffer.seek(0)
        csv_buffer.truncate(0)
        
        # Detailed runs CSV
        print("\n=== DETAILED RUNS CSV ===")
        detail_writer = csv.writer(csv_buffer)
        detail_writer.writerow([
            "group_key", "run_id", "name", "status", "total_tokens", "total_cost",
            "start_time", "end_time", "duration_seconds", "tags", "parent_run_id", "error"
        ])
        
        for group_key, group_runs in grouped_runs.items():
            for run in group_runs:
                detail_writer.writerow([
                    group_key,
                    str(run.id) if run.id else "",
                    str(run.name) if run.name else "",
                    str(run.status) if run.status else "",
                    int(run.total_tokens) if run.total_tokens else 0,
                    float(run.total_cost) if run.total_cost else 0.0,
                    run.start_time.isoformat() if run.start_time else "",
                    run.end_time.isoformat() if run.end_time else "",
                    (run.end_time - run.start_time).total_seconds() if run.start_time and run.end_time else "",
                    "|".join(run.tags) if run.tags else "",
                    str(run.parent_run_id) if run.parent_run_id else "",
                    str(run.error) if run.error else ""
                ])
        
        #print(csv_buffer.getvalue())

if __name__ == "__main__":
    metrics = LangChainMetrics()
    runs = metrics.get_latest_runs(limit=10)
    metrics.pretty_print_metrics(runs, group_by="parent_id")