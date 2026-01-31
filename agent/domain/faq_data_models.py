from typing import List, Dict, Optional
from pydantic import BaseModel

class FAQItemData(BaseModel):
    question: str
    patterns: List[str]
    answer: str
    category: str

class FAQResponses(BaseModel):
    greeting: Optional[str] = None
    farewell: Optional[str] = None
    gratitude: Optional[str] = None
    assistant_info: Optional[str] = None
    help_request: Optional[str] = None
    # Allow extra fields for other responses if needed
    model_config = {"extra": "allow"}

class FAQData(BaseModel):
    greeting_patterns: List[str]
    farewell_patterns: List[str]
    gratitude_patterns: List[str]
    assistant_info_patterns: List[str]
    help_request_patterns: List[str]
    responses: FAQResponses
    faq_items: List[FAQItemData]

class DocumentChunk(BaseModel):
    content: str
    category: str
    metadata: Dict
