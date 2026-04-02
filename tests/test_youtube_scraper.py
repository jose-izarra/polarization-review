import os
import unittest
from unittest.mock import MagicMock, patch


class _FakeHttpError(Exception):
    """Minimal stand-in for googleapiclient.errors.HttpError."""

    def __init__(self, status_code: int):
        super().__init__(f"HttpError {status_code}")
        self.status_code = status_code


def _make_search_response(video_ids: list[str]) -> dict:
    return {
        "items": [
            {
                "id": {"videoId": vid},
                "snippet": {
                    "title": f"Video {vid}",
                    "description": f"Description for {vid}",
                    "publishedAt": "2026-01-01T00:00:00Z",
                },
            }
            for vid in video_ids
        ]
    }


def _make_comments_response(video_id: str, n: int) -> dict:
    return {
        "items": [
            {
                "snippet": {
                    "topLevelComment": {
                        "id": f"comment_{video_id}_{i}",
                        "snippet": {
                            "textDisplay": f"Comment {i} on {video_id}",
                            "publishedAt": "2026-01-02T00:00:00Z",
                            "likeCount": i,
                        },
                    }
                }
            }
            for i in range(n)
        ]
    }


def _build_mock_youtube(
    video_ids: list[str], comments_per_video: int = 2, disabled_ids: set | None = None
):
    disabled = disabled_ids or set()
    youtube = MagicMock()

    # search().list().execute()
    search_list = MagicMock()
    search_list.execute.return_value = _make_search_response(video_ids)
    youtube.search.return_value.list.return_value = search_list

    # commentThreads().list().execute()  — per video_id
    def comment_list_side_effect(**kwargs):
        vid = kwargs["videoId"]
        mock = MagicMock()
        if vid in disabled:
            mock.execute.side_effect = _FakeHttpError(403)
        else:
            mock.execute.return_value = _make_comments_response(vid, comments_per_video)
        return mock

    youtube.commentThreads.return_value.list.side_effect = comment_list_side_effect
    return youtube


class TestCollectYoutubeData(unittest.TestCase):
    def setUp(self):
        os.environ["YOUTUBE_API_KEY"] = "fake-key"

    def tearDown(self):
        os.environ.pop("YOUTUBE_API_KEY", None)

    @patch("src.internal.pipeline.scrape.youtube.fetch._fetch_transcript", return_value=None)
    @patch("src.internal.pipeline.scrape.youtube.fetch._build_youtube_client")
    def test_happy_path_returns_posts_and_comments(self, mock_build, mock_transcript):
        mock_build.return_value = _build_mock_youtube(
            ["v1", "v2"], comments_per_video=2
        )

        from src.internal.pipeline.scrape.youtube.fetch import collect_youtube_data

        result = collect_youtube_data("test query")
        data = result["data"]

        self.assertEqual(len(data["posts"]), 2)
        self.assertEqual(len(data["comments"]), 4)  # 2 videos × 2 comments

    @patch("src.internal.pipeline.scrape.youtube.fetch._fetch_transcript", return_value=None)
    @patch("src.internal.pipeline.scrape.youtube.fetch._build_youtube_client")
    def test_post_raw_item_shape(self, mock_build, mock_transcript):
        mock_build.return_value = _build_mock_youtube(["vid123"], comments_per_video=0)

        from src.internal.pipeline.scrape.youtube.fetch import collect_youtube_data

        result = collect_youtube_data("topic")
        post = result["data"]["posts"][0]

        self.assertEqual(post["platform_id"], "youtube_video_vid123")
        self.assertEqual(post["source"], "youtube")
        self.assertIn("vid123", post["url"])
        self.assertEqual(post["metadata"]["content_type"], "post")
        self.assertIn("engagement", post)
        self.assertIn("timestamp", post)

    @patch("src.internal.pipeline.scrape.youtube.fetch._fetch_transcript", return_value=None)
    @patch("src.internal.pipeline.scrape.youtube.fetch._build_youtube_client")
    def test_comment_has_parent_video_id(self, mock_build, mock_transcript):
        mock_build.return_value = _build_mock_youtube(["vid123"], comments_per_video=1)

        from src.internal.pipeline.scrape.youtube.fetch import collect_youtube_data

        result = collect_youtube_data("topic")
        comment = result["data"]["comments"][0]

        self.assertTrue(comment["platform_id"].startswith("youtube_comment_"))
        self.assertEqual(comment["source"], "youtube")
        self.assertEqual(comment["metadata"]["content_type"], "comment")
        self.assertEqual(comment["metadata"]["parent_video_id"], "vid123")

    @patch(
        "src.internal.pipeline.scrape.youtube.fetch._fetch_transcript",
        return_value="This is a transcript",
    )
    @patch("src.internal.pipeline.scrape.youtube.fetch._build_youtube_client")
    def test_transcript_stored_in_metadata(self, mock_build, mock_transcript):
        mock_build.return_value = _build_mock_youtube(["vid1"], comments_per_video=0)

        from src.internal.pipeline.scrape.youtube.fetch import collect_youtube_data

        result = collect_youtube_data("topic")
        post = result["data"]["posts"][0]

        self.assertEqual(post["metadata"]["transcript"], "This is a transcript")

    @patch("src.internal.pipeline.scrape.youtube.fetch._fetch_transcript", return_value=None)
    @patch("src.internal.pipeline.scrape.youtube.fetch._build_youtube_client")
    def test_comments_disabled_skips_video_continues(self, mock_build, mock_transcript):
        mock_build.return_value = _build_mock_youtube(
            ["v1", "v2"], comments_per_video=3, disabled_ids={"v1"}
        )

        from src.internal.pipeline.scrape.youtube.fetch import collect_youtube_data

        result = collect_youtube_data("topic")
        # v1 comments disabled → 0 comments; v2 has 3
        self.assertEqual(len(result["data"]["posts"]), 2)
        self.assertEqual(len(result["data"]["comments"]), 3)

    @patch("src.internal.pipeline.scrape.youtube.fetch._fetch_transcript", return_value=None)
    @patch("src.internal.pipeline.scrape.youtube.fetch._build_youtube_client")
    def test_empty_video_results(self, mock_build, mock_transcript):
        youtube = MagicMock()
        youtube.search.return_value.list.return_value.execute.return_value = {
            "items": []
        }
        mock_build.return_value = youtube

        from src.internal.pipeline.scrape.youtube.fetch import collect_youtube_data

        result = collect_youtube_data("obscure query")
        self.assertEqual(result["data"]["posts"], [])
        self.assertEqual(result["data"]["comments"], [])

    @patch("src.internal.pipeline.scrape.youtube.fetch._fetch_transcript", return_value=None)
    @patch("src.internal.pipeline.scrape.youtube.fetch._build_youtube_client")
    def test_config_max_videos_respected(self, mock_build, mock_transcript):
        youtube = _build_mock_youtube(["v1", "v2", "v3"], comments_per_video=0)
        called_with = {}

        def capture_list(**kwargs):
            called_with.update(kwargs)
            m = MagicMock()
            m.execute.return_value = _make_search_response(["v1"])
            return m

        youtube.search.return_value.list.side_effect = capture_list
        mock_build.return_value = youtube

        from src.internal.pipeline.scrape.youtube.fetch import collect_youtube_data

        collect_youtube_data(
            "query", config={"max_videos": 5, "max_comments_per_video": 0}
        )
        self.assertEqual(called_with["maxResults"], 5)

    @patch("src.internal.pipeline.scrape.youtube.fetch._fetch_transcript", return_value=None)
    @patch("src.internal.pipeline.scrape.youtube.fetch._build_youtube_client")
    def test_config_max_comments_per_video_respected(self, mock_build, mock_transcript):
        youtube = _build_mock_youtube(["v1"], comments_per_video=10)
        called_with = {}

        def capture_list(**kwargs):
            called_with.update(kwargs)
            return MagicMock(
                execute=MagicMock(return_value=_make_comments_response("v1", 3))
            )

        youtube.commentThreads.return_value.list.side_effect = capture_list
        mock_build.return_value = youtube

        from src.internal.pipeline.scrape.youtube.fetch import collect_youtube_data

        collect_youtube_data(
            "query", config={"max_videos": 1, "max_comments_per_video": 7}
        )
        self.assertEqual(called_with["maxResults"], 7)

    def test_missing_api_key_raises(self):
        os.environ.pop("YOUTUBE_API_KEY", None)

        from src.internal.pipeline.scrape.youtube.fetch import collect_youtube_data

        with self.assertRaises(RuntimeError, msg="YOUTUBE_API_KEY"):
            collect_youtube_data("anything")


if __name__ == "__main__":
    unittest.main()
