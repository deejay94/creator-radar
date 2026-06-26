import pytest

from radar.connectors.types import Opportunity
from radar.opportunity_filters import get_male_only_creator_filter_reason


def _opp(title: str, description: str = "") -> Opportunity:
    return Opportunity(
        platform="upwork",
        external_id="test12345678",
        title=title,
        description=description,
        url="https://www.upwork.com/jobs/~test12345678",
    )


def test_filters_male_only_ugc_creator():
    reason = get_male_only_creator_filter_reason(
        _opp("Male UGC Creator Needed", "Looking for a male content creator for TikTok.")
    )
    assert reason == "male-targeted opportunity (no female-inclusive language)"


def test_keeps_when_female_also_mentioned():
    assert get_male_only_creator_filter_reason(
        _opp("UGC Creators", "Seeking male and female UGC creators for our campaign.")
    ) is None


def test_keeps_female_only():
    assert get_male_only_creator_filter_reason(
        _opp("Female UGC Creator", "We need a female creator for product videos.")
    ) is None


def test_keeps_gender_neutral():
    assert get_male_only_creator_filter_reason(
        _opp("UGC Creator for Skincare Brand", "Looking for creators to film testimonials.")
    ) is None


def test_filters_men_only_phrase():
    assert get_male_only_creator_filter_reason(
        _opp("Content creators wanted", "Men only. Must have beard.")
    ) == "male-targeted opportunity (no female-inclusive language)"


def test_does_not_false_positive_on_female_word():
    assert get_male_only_creator_filter_reason(
        _opp("Female skincare UGC", "Looking for female creators.")
    ) is None


def test_filters_mens_wellness_without_female_language():
    assert get_male_only_creator_filter_reason(
        _opp(
            "UGC Creator for Men's Wellness Brand",
            "We need short-form videos for our men's wellness supplement line.",
        )
    ) == "male-targeted opportunity (no female-inclusive language)"


def test_keeps_mens_wellness_when_women_included():
    assert get_male_only_creator_filter_reason(
        _opp(
            "UGC Creators",
            "Content for women's and men's wellness product lines.",
        )
    ) is None


def test_filters_for_men_phrase():
    assert get_male_only_creator_filter_reason(
        _opp("UGC Video Creator", "Beard care brand for men. Looking for creators.")
    ) == "male-targeted opportunity (no female-inclusive language)"


def test_keeps_generic_skincare_fitness_supplements():
    assert get_male_only_creator_filter_reason(
        _opp("UGC Creator for Skincare Brand", "Looking for creators to film supplement and fitness content.")
    ) is None
    assert get_male_only_creator_filter_reason(
        _opp("Fitness UGC Videos", "Need creators for workout apparel and skincare routines.")
    ) is None
