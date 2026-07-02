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
            scope_name="??",
            stock_code="6230",
            stock_name="???",
        )

    def test_complete_source_scores_high(self):
        sources = [
            {
                "title": "????????",
                "source_name": "Official Press Release",
                "source_url": "https://example.com/high",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": (
                    "???????????? 2330 ??????????????????"
                    "????????????????????"
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
                "title": "??????",
                "source_name": "Example",
                "source_url": "",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "??????",
                "source_type": "http",
            }
        ]
        scored = score_sources(sources, self.task, self.task)
        self.assertEqual(scored[0]["quality_level"], "rejected")

    def test_prohibited_words_are_rejected(self):
        sources = [
            {
                "title": "買進建議",
                "source_name": "Bad Source",
                "source_url": "https://example.com/bad",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "法人建議買進，並給出明確目標價與報酬率預估。",
                "source_type": "search",
            }
        ]
        scored = score_sources(sources, self.task, self.task)
        self.assertEqual(scored[0]["quality_level"], "rejected")
        self.assertTrue(scored[0]["quality_reasons"])

    def test_quote_style_bulletin_is_rejected_for_non_target_context(self):
        sources = [
            {
                "title": "?????? 2330 ?? 7.01%",
                "source_name": "Yahoo Finance",
                "source_url": "https://example.com/quote-bulletin",
                "published_at": "2026-06-25T10:00:00+08:00",
                "content": "????????????????????????????",
                "source_type": "search",
            }
        ]
        scored = score_sources(sources, {"scope": "macro", "scope_name": "???"}, {"scope": "macro"})
        self.assertEqual(scored[0]["quality_level"], "rejected")
        self.assertTrue(
            any("quote-style" in reason or "stock price bulletin" in reason for reason in scored[0]["quality_reasons"])
        )

    def test_yahoo_stock_article_with_target_mentions_is_kept(self):
        sources = [
            {
                "title": "???????",
                "source_name": "Yahoo News",
                "source_url": "https://tw.stock.yahoo.com/news/tsmc-expansion-1.html",
                "published_at": "2026-06-25T10:00:00+08:00",
                "content": "??? 2330 ??????????????????????????",
                "source_type": "http",
            }
        ]
        filtered = filter_sources({"raw_sources": sources, **self.task})
        self.assertEqual(len(filtered["filtered_sources"]), 1)
        self.assertIn(filtered["filtered_sources"][0]["quality_level"], {"high", "medium", "low"})

    def test_duplicate_source_url_keeps_only_one(self):
        sources = [
            {
                "title": "???? A",
                "source_name": "RSS A",
                "source_url": "https://example.com/dup",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "?????? A?",
                "source_type": "rss",
            },
            {
                "title": "???? B",
                "source_name": "RSS B",
                "source_url": "https://example.com/dup",
                "published_at": "2026-06-17T09:00:00+08:00",
                "content": "?????? B?",
                "source_type": "rss",
            },
        ]
        filtered = filter_sources({"raw_sources": sources, **self.task})
        self.assertEqual(len(filtered["filtered_sources"]), 1)
        self.assertEqual(filtered["quality_summary"]["rejected"], 1)

    def test_high_and_medium_sources_enter_filtered_sources(self):
        sources = [
            {
                "title": "??????",
                "source_name": "Official Press Release",
                "source_url": "https://example.com/high",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "?????????????????????",
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
                "title": "重大更新",
                "source_name": "Bad",
                "source_url": "https://example.com/rejected",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "法人建議買進，目標價與報酬率預估明確。",
                "source_type": "search",
            },
            {
                "title": "??????",
                "source_name": "Good",
                "source_url": "https://example.com/good",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": "?????????????????",
                "source_type": "rss",
            },
        ]
        filtered = filter_sources({"raw_sources": sources, **self.task})
        urls = {source["source_url"] for source in filtered["filtered_sources"]}
        self.assertNotIn("https://example.com/rejected", urls)

    def test_quality_summary_counts_are_correct(self):
        sources = [
            {
                "title": "散熱產業研究更新",
                "source_name": "Official Press Release",
                "source_url": "https://example.com/high",
                "published_at": "2026-06-17T08:00:00+08:00",
                "content": (
                    "散熱產業出貨改善，6230 尼得科超眾與供應鏈同步更新。"
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
                "title": "買進建議",
                "source_name": "Bad",
                "source_url": "https://example.com/rejected",
                "published_at": "2026-06-17T09:00:00+08:00",
                "content": "法人建議買進，並喊出新的目標價。",
                "source_type": "search",
            },
        ]
        filtered = filter_sources({"raw_sources": sources, **self.task})
        self.assertEqual(filtered["quality_summary"]["total_sources"], 3)
        self.assertEqual(filtered["quality_summary"]["rejected"], 1)
        self.assertGreaterEqual(filtered["quality_summary"]["high"], 1)


if __name__ == "__main__":
    unittest.main()
