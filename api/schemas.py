from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from api.response import ApiEnvelope


BatchName = Literal["industries", "stocks", "macro", "institution_watch", "all"]
RunMode = Literal["daily", "three_day"]
SourceMode = Literal["mock", "rss", "http", "search", "hybrid"]
SummarizerMode = Literal["mock", "llm", "auto"]
LlmProvider = Literal["auto", "openai", "gemini", "mock"]
SearchProvider = Literal["auto", "mock", "tavily", "serpapi"]
PacketTypeFilter = Literal["all", "event", "daily_digest", "report", "crawl_run", "rejected_source"]


class CollectRunRequest(BaseModel):
    mode: RunMode = "daily"
    scope: str | None = None
    scope_name: str | None = None
    stock_code: str = ""
    stock_name: str = ""
    source_mode: SourceMode = "mock"
    summarizer_mode: SummarizerMode = "mock"
    llm_provider: LlmProvider = "auto"
    search_provider: SearchProvider = "auto"
    batch: BatchName | None = None
    dry_run: bool = False


class CollectRunResponse(ApiEnvelope):
    message: str = "Collector run completed."


class IngestionRunRequest(BaseModel):
    input_path: str = "output/"
    packet_type: PacketTypeFilter = "all"
    dry_run: bool = True


class IngestionRunResponse(ApiEnvelope):
    message: str = "Ingestion run completed."


class PromotionRunRequest(BaseModel):
    input_path: str = "output/"
    packet_type: PacketTypeFilter = "all"
    dry_run: bool = True


class PromotionRunResponse(ApiEnvelope):
    message: str = "Promotion run completed."


class PipelineCollectRequest(CollectRunRequest):
    enabled: bool = True


class PipelineIngestionRequest(IngestionRunRequest):
    enabled: bool = True


class PipelinePromotionRequest(PromotionRunRequest):
    enabled: bool = True


class PipelineRunRequest(BaseModel):
    mode: RunMode = "daily"
    scope: str = "all"
    scope_name: str | None = None
    stock_code: str = ""
    stock_name: str = ""
    source_mode: SourceMode = "hybrid"
    summarizer_mode: SummarizerMode = "auto"
    llm_provider: LlmProvider = "auto"
    search_provider: SearchProvider = "auto"
    ingestion_dry_run: bool = True
    promotion_dry_run: bool = True
    collect: PipelineCollectRequest | None = None
    ingestion: PipelineIngestionRequest | None = None
    promotion: PipelinePromotionRequest | None = None


class PipelineRunResponse(ApiEnvelope):
    autonomous_ready: bool = False
    collect_ran: bool = False
    ingestion_ran: bool = False
    promotion_ran: bool = False
    wrote_to_supabase: bool = False
    message: str = "Pipeline completed."
