from unittest.mock import patch

from radar.connectors.types import Opportunity, SearchParams
from radar.db.import_service import import_opportunities
from radar.db.repository import OpportunityRepository


def test_import_scores_before_insert(tmp_path):
    repo = OpportunityRepository(tmp_path / "scored.db")

    from unittest.mock import MagicMock

    connector = MagicMock()
    connector.platform = "upwork"
    connector.health_check.return_value = MagicMock(healthy=True, message="ok")

    opportunity = Opportunity(
        platform="upwork",
        external_id="job1234567890",
        title="UGC Creator",
        url="https://www.upwork.com/jobs/~job1234567890",
    )

    scored = opportunity.model_copy(
        update={"ai_score": 90, "priority": "high", "reasoning": "Great fit"}
    )

    def pipeline(_connector, _params, on_extraction_error=None):
        yield opportunity

    with patch("radar.db.import_service.run_connector_pipeline", side_effect=pipeline):
        with patch("radar.db.import_service._maybe_score", return_value=scored):
            stats = import_opportunities(
                connector,
                SearchParams(queries=["UGC"]),
                repo,
                score_enabled=True,
            )

    assert stats.imported == 1
    assert stats.scored == 1
    stored = repo.get_by_platform_id("upwork", "job1234567890")
    assert stored is not None
    assert stored.ai_score == 90
    repo.close()
