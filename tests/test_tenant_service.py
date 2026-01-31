import unittest
import asyncio
from unittest.mock import MagicMock, patch
from services.tenant_data_service import TenantDataService
from agent.domain.faq_data_models import FAQData, DocumentChunk
import pandas as pd
from io import StringIO
from pathlib import Path

# Mock data for FAQs
mock_faq_csv_content = """type,patterns,response,category
greeting,"hi;;;hello","Hello there!",greeting
farewell,"bye;;;see ya","Good bye!",farewell
faq,"what is this?;;;explain","This is a test","general_info"
"""

# Mock data for Chunks
mock_chunks_csv_content = """category,text
company_info,"We are a great company."
policies,"No refunds."
"""

class TestTenantDataService(unittest.TestCase):
    def test_read_faqs_csv(self):
        async def run_test():
             with patch("services.tenant_data_service.Path") as mock_path:
                mock_path_obj = MagicMock()
                mock_path_obj.exists.return_value = True
                mock_path.return_value = mock_path_obj
                
                # Create the dataframe locally to verify it works
                # Must do this BEFORE patching pd.read_csv
                expected_df = pd.read_csv(StringIO(mock_faq_csv_content))
                
                # Patch pd inside the service module
                with patch("services.tenant_data_service.pd.read_csv") as mock_read_csv:
                    print(f"DEBUG: Dataframe shape: {expected_df.shape}")
                    mock_read_csv.return_value = expected_df
                    
                    faq_data = await TenantDataService.read_faqs_csv("test_tenant")
                    
                    mock_read_csv.assert_called()
                    
                    self.assertIsInstance(faq_data, FAQData)
                    self.assertEqual(len(faq_data.greeting_patterns), 2)
                    self.assertIn("hi", faq_data.greeting_patterns)
                    self.assertEqual(faq_data.responses.greeting, "Hello there!")
                    self.assertEqual(len(faq_data.faq_items), 1)
                    self.assertEqual(faq_data.faq_items[0].question, "General Info")

        asyncio.run(run_test())

    def test_read_chunks_csv(self):
        async def run_test():
            with patch("services.tenant_data_service.Path") as mock_path:
                mock_path_obj = MagicMock()
                mock_path_obj.exists.return_value = True
                mock_path.return_value = mock_path_obj
                
                expected_df = pd.read_csv(StringIO(mock_chunks_csv_content))
                
                with patch("services.tenant_data_service.pd.read_csv") as mock_read_csv:
                    mock_read_csv.return_value = expected_df
                    
                    chunks = await TenantDataService.read_chunks_csv("test_tenant")
                    
                    mock_read_csv.assert_called()
                    
                    self.assertEqual(len(chunks), 2)
                    self.assertIsInstance(chunks[0], DocumentChunk)
                    self.assertEqual(chunks[0].category, "company_info")
                    self.assertEqual(chunks[0].content, "We are a great company.")
        
        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
