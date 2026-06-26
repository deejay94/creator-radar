from radar.connectors.types import Opportunity
from radar.db.dedup import DedupSession, check_duplicate, check_duplicate_in_repo
from radar.db.repository import OpportunityRepository
from radar.db.similarity import descriptions_are_similar, titles_are_similar


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
    assert check_duplicate_in_repo(same_id, repo).is_duplicate
    assert check_duplicate_in_repo(same_id, repo).reason == "platform+external_id"

    same_url = Opportunity(
        platform="upwork",
        external_id="differentid1",
        title="Duplicate URL",
        url="https://www.upwork.com/jobs/~job1234567890",
    )
    assert check_duplicate_in_repo(same_url, repo).is_duplicate
    assert check_duplicate_in_repo(same_url, repo).reason == "url"

    new_opp = Opportunity(
        platform="upwork",
        external_id="job0987654321",
        title="New Job",
        url="https://www.upwork.com/jobs/~job0987654321",
    )
    assert not check_duplicate_in_repo(new_opp, repo).is_duplicate
    repo.close()


def test_dedup_title_similarity_in_database(tmp_path):
    repo = OpportunityRepository(tmp_path / "dedup.db")
    repo.insert(
        Opportunity(
            platform="upwork",
            external_id="job1111111111",
            title="UGC Creator for Skincare Brand",
            description="Need short videos for ads.",
            url="https://www.upwork.com/jobs/~job1111111111",
        )
    )

    near_duplicate = Opportunity(
        platform="upwork",
        external_id="job2222222222",
        title="UGC creator for skincare brand!",
        description="Totally different body text here.",
        url="https://www.upwork.com/jobs/~job2222222222",
    )
    result = check_duplicate_in_repo(near_duplicate, repo)
    assert result.is_duplicate
    assert result.reason == "title_similarity"
    assert result.matched_external_id == "job1111111111"
    repo.close()


def test_dedup_description_similarity_in_database(tmp_path):
    long_description = (
        "We are looking for experienced UGC creators to produce short-form product videos "
        "for TikTok and Instagram Reels. You will receive products by mail and film "
        "authentic testimonials in a natural home setting."
    )
    repo = OpportunityRepository(tmp_path / "dedup.db")
    repo.insert(
        Opportunity(
            platform="upwork",
            external_id="job1111111111",
            title="Original Title",
            description=long_description,
            url="https://www.upwork.com/jobs/~job1111111111",
        )
    )

    near_duplicate = Opportunity(
        platform="upwork",
        external_id="job2222222222",
        title="Different title entirely",
        description=long_description + " Please apply with your portfolio.",
        url="https://www.upwork.com/jobs/~job2222222222",
    )
    result = check_duplicate_in_repo(near_duplicate, repo)
    assert result.is_duplicate
    assert result.reason == "description_similarity"
    repo.close()


def test_batch_dedup_within_import_run(tmp_path):
    repo = OpportunityRepository(tmp_path / "dedup.db")
    session = DedupSession(repo=repo)

    first = Opportunity(
        platform="upwork",
        external_id="job1111111111",
        title="UGC Creator Needed",
        description="Short description",
        url="https://www.upwork.com/jobs/~job1111111111",
    )
    assert not check_duplicate(first, session).is_duplicate
    session.record(first)

    second = Opportunity(
        platform="upwork",
        external_id="job2222222222",
        title="UGC creator needed",
        description="Another post",
        url="https://www.upwork.com/jobs/~job2222222222",
    )
    result = check_duplicate(second, session)
    assert result.is_duplicate
    assert result.reason == "batch:title_similarity"
    repo.close()


def test_similarity_helpers():
    assert titles_are_similar("UGC Creator Needed", "UGC creator needed!")
    assert descriptions_are_similar(
        "We need UGC creators to film product testimonials at home with natural lighting and clear audio.",
        "We need UGC creators to film product testimonials at home with natural lighting and clear audio please apply.",
    )
