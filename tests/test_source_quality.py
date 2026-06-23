from __future__ import annotations

import unittest

from collector.nodes.filter import filter_sources
from collector.quality.source_scorer import score_sources, summarize_quality
from collector.schemas.crawl_run_packet import build_crawl_run_packet
from collector.tasks import make_task


class SourceQualityScoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = make_task(
            scope="industry",
            scope_name="散熱",
            stock_code="6230",
            stock_name="尼得科超眾",
        )

    def test_complete_source_scores_high(self):
        sources = [
            {
                "title": "散熱產業出貨改善與供應鏈更新",
                "source_name": "Official Press Release",
                "source_url": "https://example.com/high",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": (
                    "散熱產業出貨改善，6230 尼得科超眾與供應鏈同步更新，"
                    "本篇內容聚焦研究、公告、出貨與需求變化，"
                    "並說明相關供應鏈執行進度與產業觀察。"
                ),
                "source_type": "rss",
            }
        ]
        scored = score_sources(sources, self.task, self.task)
        self.assertEqual(scored[0]["quality_level"], "high")
        self.assertGreaterEqual(scored[0]["quality_score"], 80)

    def test_missing_source_url_is_rejected(self):
        sources = [
            {
                "title": "散熱產業觀察",
                "source_name": "Example",
                "source_url": "",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "這是一則研究內容。",
                "source_type": "http",
            }
        ]
        scored = score_sources(sources, self.task, self.task)
        self.assertEqual(scored[0]["quality_level"], "rejected")

    def test_prohibited_words_are_rejected(self):
        sources = [
            {
                "title": "買進 散熱股",
                "source_name": "Bad Source",
                "source_url": "https://example.com/bad",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "建議買進、目標價上看，屬於喊單內容。",
                "source_type": "search",
            }
        ]
        scored = score_sources(sources, self.task, self.task)
        self.assertEqual(scored[0]["quality_level"], "rejected")
        self.assertTrue(scored[0]["quality_reasons"])

    def test_duplicate_source_url_keeps_only_one(self):
        sources = [
            {
                "title": "散熱報導 A",
                "source_name": "RSS A",
                "source_url": "https://example.com/dup",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "散熱供應鏈研究內容，資料完整且可靠。",
                "source_type": "rss",
            },
            {
                "title": "散熱報導 B",
                "source_name": "RSS B",
                "source_url": "https://example.com/dup",
                "published_at": "2026-06-17T09:00:00+08:00",
                "content": "另一筆重複內容。",
                "source_type": "rss",
            },
        ]
        filtered = filter_sources({"raw_sources": sources, **self.task})
        self.assertEqual(len(filtered["filtered_sources"]), 1)
        self.assertEqual(filtered["quality_summary"]["rejected"], 1)

    def test_high_and_medium_sources_enter_filtered_sources(self):
        sources = [
            {
                "title": "散熱產業研究",
                "source_name": "Official Press Release",
                "source_url": "https://example.com/high",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": (
                    "散熱產業出貨改善，6230 尼得科超眾與供應鏈同步更新，"
                    "本篇內容聚焦研究、公告、出貨與需求變化，"
                    "並說明相關供應鏈執行進度與產業觀察。"
                ),
                "source_type": "rss",
            },
            {
                "title": "Industry note",
                "source_name": "News Feed",
                "source_url": "https://example.com/medium",
                "published_at": "2026-06-17T08:10:00+08:00",
                "content": "This article provides a plain market note on logistics and operations without explicit keywords.",
                "source_type": "http",
            },
        ]
        filtered = filter_sources({"raw_sources": sources, **self.task})
        self.assertEqual(len(filtered["filtered_sources"]), 2)
        self.assertGreaterEqual(
            filtered["filtered_sources"][0]["quality_score"],
            filtered["filtered_sources"][1]["quality_score"],
        )

    def test_rejected_sources_do_not_enter_filtered_sources(self):
        sources = [
            {
                "title": "散熱喊單",
                "source_name": "Bad",
                "source_url": "https://example.com/rejected",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "建議買進、目標價上看。",
                "source_type": "search",
            },
            {
                "title": "散熱研究",
                "source_name": "Good",
                "source_url": "https://example.com/good",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "散熱產業研究內容，屬於公告與供應鏈分析。",
                "source_type": "rss",
            },
        ]
        filtered = filter_sources({"raw_sources": sources, **self.task})
        urls = {source["source_url"] for source in filtered["filtered_sources"]}
        self.assertNotIn("https://example.com/rejected", urls)

    def test_quality_summary_counts_are_correct(self):
        sources = [
            {
                "title": "散熱高品質報導",
                "source_name": "Official Press Release",
                "source_url": "https://example.com/high",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": (
                    "散熱產業出貨改善，6230 尼得科超眾與供應鏈同步更新，"
                    "本篇內容聚焦研究、公告、出貨與需求變化，"
                    "並說明相關供應鏈執行進度與產業觀察。"
                ),
                "source_type": "rss",
            },
            {
                "title": "Industry note",
                "source_name": "News Feed",
                "source_url": "https://example.com/medium",
                "published_at": "2026-06-17T08:10:00+08:00",
                "content": "This article provides a plain market note on logistics and operations without explicit keywords.",
                "source_type": "http",
            },
            {
                "title": "Short note",
                "source_name": "Blog",
                "source_url": "https://example.com/low",
                "published_at": "",
                "content": "short content",
                "source_type": "mock",
            },
            {
                "title": "Bad content",
                "source_name": "Bad Source",
                "source_url": "",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "建議買進、目標價上看。",
                "source_type": "search",
            },
        ]
        filtered = filter_sources({"raw_sources": sources, **self.task})
        summary = filtered["quality_summary"]
        self.assertEqual(summary["total_sources"], 4)
        self.assertEqual(summary["high"], 1)
        self.assertEqual(summary["medium"], 1)
        self.assertEqual(summary["low"], 1)
        self.assertEqual(summary["rejected"], 1)

    def test_scoring_supports_mock_rss_http_and_search(self):
        sources = [
            {
                "title": "Mock source",
                "source_name": "Mock Feed",
                "source_url": "https://example.com/mock",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "Mock research content for validation.",
                "source_type": "mock",
            },
            {
                "title": "RSS source",
                "source_name": "RSS Feed",
                "source_url": "https://example.com/rss",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "RSS research content for validation.",
                "source_type": "rss",
            },
            {
                "title": "HTTP source",
                "source_name": "HTTP Article",
                "source_url": "https://example.com/http",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "HTTP research content for validation.",
                "source_type": "http",
            },
            {
                "title": "Search source",
                "source_name": "Search Result",
                "source_url": "https://example.com/search",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "Search research content for validation.",
                "source_type": "search",
            },
        ]
        scored = score_sources(sources, self.task, self.task)
        self.assertEqual(len(scored), 4)
        self.assertTrue(all("quality_score" in source for source in scored))

    def test_crawl_run_packet_includes_quality_summary(self):
        state = {
            "run_id": "run-001",
            "started_at": "2026-06-17T08:00:00+08:00",
            "raw_sources": [],
            "output_paths": ["output/daily/example.json"],
            "quality_summary": {
                "total_sources": 4,
                "high": 1,
                "medium": 1,
                "low": 1,
                "rejected": 1,
            },
            "run_errors": [],
            "validation_errors": [],
            "scope": "industry",
        }
        packet = build_crawl_run_packet(state)
        self.assertEqual(packet["quality_summary"]["rejected"], 1)


if __name__ == "__main__":
    unittest.main()
