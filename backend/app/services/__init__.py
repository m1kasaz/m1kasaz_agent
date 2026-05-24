from app.services.document_service import handle_document_request
from app.services.paper_service import recommend_paper
from app.services.storage import Storage

__all__ = ["Storage", "handle_document_request", "recommend_paper"]
