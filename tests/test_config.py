"""The real config files load, and the validation rules catch broken study files."""

import pytest
from pydantic import ValidationError

from backtester.config import Study, load_settings, load_studies


def test_settings_load():
    settings = load_settings()
    assert settings.thresholds.n_min == 3
    assert settings.exposure_roles == ["PS", "SS"]
    assert settings.headline.criterion == "evans"
    assert settings.headline.drug_key == "class"


def test_all_six_studies_load_with_one_verified_primary_action():
    studies = load_studies()
    assert len(studies) == 6
    for study in studies:
        assert study.primary_action.verified_on is not None
        assert study.primary_action.quote
        assert study.primary_action.archive_url
        assert "primary" in study.event_groups
        assert set(study.drug_group.approval_dates) == set(study.drug_group.substances)


def minimal_study(**overrides) -> dict:
    study = {
        "study_id": "x",
        "title": "X",
        "definition_status": "draft",
        "drug_group": {
            "label": "X",
            "substances": ["X"],
            "marketed_before_2004": False,
            "approval_dates": {"X": "2010-01-01"},
        },
        "event_groups": {"primary": {"label": "E", "pts": ["Nausea "]}},
        "regulatory_actions": [
            {
                "agency": "FDA",
                "date": "2020-01-01",
                "type": "DSC",
                "title": "t",
                "primary": True,
                "verified_on": "2026-10-31",
                "quote": "[1-1-2020] Safety Announcement",
                "archive_url": "http://web.archive.org/web/2020/https://example.org",
            }
        ],
    }
    study.update(overrides)
    return study


def test_pts_are_normalised_to_upper_case():
    study = Study.model_validate(minimal_study())
    assert study.event_groups["primary"].pts == ["NAUSEA"]


def test_study_without_primary_action_is_rejected():
    data = minimal_study()
    data["regulatory_actions"][0]["primary"] = False
    with pytest.raises(ValidationError, match="exactly one regulatory action must be primary"):
        Study.model_validate(data)


def test_unverified_primary_action_is_rejected():
    data = minimal_study()
    data["regulatory_actions"][0]["verified_on"] = None
    with pytest.raises(ValidationError, match="verified exact date"):
        Study.model_validate(data)


def test_primary_event_group_is_required():
    data = minimal_study(event_groups={"narrow": {"label": "E", "pts": ["NAUSEA"]}})
    with pytest.raises(ValidationError, match="must contain 'primary'"):
        Study.model_validate(data)


def test_primary_action_without_quote_is_rejected():
    data = minimal_study()
    data["regulatory_actions"][0]["quote"] = None
    with pytest.raises(ValidationError, match="needs a quote and an archive_url"):
        Study.model_validate(data)


def test_approval_dates_must_cover_every_substance():
    data = minimal_study()
    data["drug_group"]["substances"] = ["X", "Y"]
    with pytest.raises(ValidationError, match="approval_dates must list exactly"):
        Study.model_validate(data)
