from radar.connectors.types import Opportunity
from radar.db.dedup import check_duplicate
from radar.db.repository import OpportunityRepository


def test_insert_and_fetch_opportunity(tmp_path):
    db_path = tmp_path / "test.db"
    repo = OpportunityRepository(db_path)

    opp = Opportunity(
        platform="upwork",
        external_id="job1234567890",
        title="UGC Creator",
        description="Create videos",
        url="https://www.upwork.com/jobs/~job1234567890",
        budget="$500",
        hourly=False,
        skills=["TikTok"],
        client_rating="4.9",
        metadata={"search_query": "UGC"},
    )
    row_id = repo.insert(opp)
    assert row_id == 1
    assert repo.count("upwork") == 1

    loaded = repo.get_by_platform_id("upwork", "job1234567890")
    assert loaded is not None
    assert loaded.title == "UGC Creator"
    assert loaded.hourly is False
    assert loaded.skills == ["TikTok"]
    repo.close()


def test_dedup_by_platform_id_and_url(tmp_path):
    db_path = tmp_path / "test.db"
    repo = OpportunityRepository(db_path)

    opp = Opportunity(
        platform="upwork",
        external_id="job1234567890",
        title="UGC Creator",
        url="https://www.upwork.com/jobs/~job1234567890",
    )
    repo.insert(opp)

    same_id = Opportunity(
        platform="upwork",
        external_id="job1234567890",
        title="Duplicate",
        url="https://www.upwork.com/jobs/~job1234567890",
    )
    assert check_duplicate(same_id, repo).is_duplicate
    assert check_duplicate(same_id, repo).reason == "platform+external_id"

    same_url = Opportunity(
        platform="upwork",
        external_id="differentid1",
        title="Duplicate URL",
        url="https://www.upwork.com/jobs/~job1234567890",
    )
    assert check_duplicate(same_url, repo).is_duplicate
    assert check_duplicate(same_url, repo).reason == "url"

    new_opp = Opportunity(
        platform="upwork",
        external_id="job0987654321",
        title="New Job",
        url="https://www.upwork.com/jobs/~job0987654321",
    )
    assert not check_duplicate(new_opp, repo).is_duplicate
    repo.close()
