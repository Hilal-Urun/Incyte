import io
from dotenv import load_dotenv
load_dotenv()

from env_check import check_required_env_vars, check_optional_env_vars
check_required_env_vars()
check_optional_env_vars()

from sharepoint.sharepoint_client import IncyteSPDoc
from sharepoint.sharepoint_crawler import IncyteSharepointCrawler

doc = IncyteSPDoc(
    Path="dummy",
    DocId="dummy",
    ContentBuffer=io.BytesIO(open("src/tests/test_data/bellacosa1996.pdf", "rb").read()),
    FileType="pdf",
    LastModifiedTime="dummy",
    Title="dummy"
)

crawler = IncyteSharepointCrawler()
crawler.process_sp_doc(doc)

# Path: src\sharepoint\sharepoint_client.py
