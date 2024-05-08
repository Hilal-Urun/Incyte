from dotenv import load_dotenv
load_dotenv()
from env_check import check_required_env_vars, check_optional_env_vars
check_required_env_vars()
check_optional_env_vars()

from indexing.meilisearch.meilisearch_client import MeilisearchClient

meilisearch_client = MeilisearchClient()

meilisearch_client.configure_settings()

print(meilisearch_client.search("cancer", 0, 10))

