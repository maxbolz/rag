import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ClickHouse Configuration
CLICKHOUSE_CONFIG = {
    'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
    'port': int(os.getenv('CLICKHOUSE_PORT', 8123)),
    'username': os.getenv('CLICKHOUSE_USERNAME', 'default'),
    'password': os.getenv('CLICKHOUSE_PASSWORD', ''),
    'database': os.getenv('CLICKHOUSE_DATABASE', 'default')
}

# Required environment variables
REQUIRED_ENV_VARS = [
    'CLICKHOUSE_HOST',
    'CLICKHOUSE_PORT', 
    'CLICKHOUSE_USERNAME',
    'CLICKHOUSE_PASSWORD',
    'CLICKHOUSE_DATABASE'
] 