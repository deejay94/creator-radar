from radar.upwork.api_extract import extract_jobs_from_payload, merge_job_items


def test_extract_jobs_from_graphql_payload():
    payload = {
        "data": {
            "marketplaceJobPostingsSearch": {
                "results": [
                    {
                        "id": "~01abcdefghij",
                        "title": "UGC Creator for TikTok",
                        "url": "/jobs/~01abcdefghij",
                    }
                ]
            }
        }
    }
    jobs = extract_jobs_from_payload(payload)
    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "01abcdefghij"
    assert jobs[0]["title"] == "UGC Creator for TikTok"


def test_merge_job_items_dedupes():
    dom = [{"external_id": "abc1234567", "title": "Job A", "url": "https://example.com/a"}]
    api = [{"external_id": "abc1234567", "title": "Job A duplicate", "url": "https://example.com/b"}]
    merged = merge_job_items(dom, api)
    assert len(merged) == 1
    assert merged[0]["title"] == "Job A"
