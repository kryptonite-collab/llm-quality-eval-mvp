"""RAG API schemas."""

from typing import Any

from pydantic import BaseModel, Field


class RAGSearchRequest(BaseModel):
    """Parameters for a vector search query."""

    collection_name: str = Field("documents", description="Target collection for search")
    collection_names: list[str] | None = Field(
        None, description="Search across multiple collections (overrides collection_name)"
    )
    query: str = Field(..., description="Natural language search query")
    limit: int = Field(default=4, ge=1, le=20)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    filter: str | None = Field(
        None, description="Scalar filter expression (e.g. 'filetype == \"pdf\"')"
    )


class RAGSearchResult(BaseModel):
    """A single retrieved chunk with its associated metadata."""

    content: str
    score: float
    metadata: dict[str, Any]
    parent_doc_id: str


class RAGSearchResponse(BaseModel):
    """List of results found in the vector store."""

    results: list[RAGSearchResult]


class RAGCollectionInfo(BaseModel):
    """Statistical information about a specific collection."""

    name: str
    total_vectors: int
    dim: int
    indexing_status: str = "complete"


class RAGCollectionList(BaseModel):
    """List of all available collection names."""

    items: list[str]


class RAGDocumentItem(BaseModel):
    """Information about a single document in a collection."""

    document_id: str = Field(..., description="Unique identifier of the document")
    filename: str | None = Field(None, description="Original filename of the document")
    filesize: int | None = Field(None, description="Size of the file in bytes")
    filetype: str | None = Field(None, description="MIME type of the file")
    chunk_count: int = Field(default=0, description="Number of chunks/vectors in the collection")
    additional_info: dict[str, Any] | None = Field(None, description="Additional metadata")


class RAGDocumentList(BaseModel):
    """List of all documents in a collection."""

    items: list[RAGDocumentItem]
    total: int = Field(..., description="Total number of unique documents")


class RAGMessageResponse(BaseModel):
    """Simple message response."""

    message: str

# Compatibility schemas for tracked RAG documents.
# These models are used by app/services/rag_document.py.

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RAGTrackedDocumentItem(BaseModel):
    id: int
    collection_name: str
    filename: str | None = None
    original_filename: str | None = None
    file_path: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    status: str | None = None
    chunk_count: int | None = 0
    has_file: bool | None = None
    metadata: dict[str, Any] | None = Field(default=None)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RAGTrackedDocumentList(BaseModel):
    items: list[RAGTrackedDocumentItem]
    total: int

# Compatibility schemas for RAG sync / ingest APIs.
# These are minimal models to fix generated-template import errors first.

from pydantic import ConfigDict


class _RAGCompatBaseModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class RAGSyncLogItem(_RAGCompatBaseModel):
    id: int | str | None = None
    document_id: int | str | None = None
    collection_name: str | None = None
    filename: str | None = None
    action: str | None = None
    status: str | None = None
    message: str | None = None
    error: str | None = None
    chunk_count: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RAGSyncLogList(_RAGCompatBaseModel):
    items: list[RAGSyncLogItem] = Field(default_factory=list)
    total: int = 0


class RAGSyncRequest(_RAGCompatBaseModel):
    collection_name: str | None = None
    document_ids: list[int] | None = None
    force: bool = False


class RAGSyncResponse(_RAGCompatBaseModel):
    status: str = "ok"
    message: str | None = None
    synced: int = 0
    failed: int = 0
    logs: list[RAGSyncLogItem] = Field(default_factory=list)


class RAGIngestResponse(_RAGCompatBaseModel):
    status: str = "ok"
    message: str | None = None
    document_id: int | str | None = None
    collection_name: str | None = None
    chunks: int | None = None


class RAGRetryResponse(_RAGCompatBaseModel):
    status: str = "ok"
    message: str | None = None
    retried: int = 0
    failed: int = 0