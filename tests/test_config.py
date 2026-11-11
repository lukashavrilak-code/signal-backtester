"""The real config files load, and the validation rules catch broken study files."""

import pytest
from pydantic import ValidationError

from backtester.config import Study, load_settings, load_studies


def test_settings_load():
    settings = load_settings()
    assert settings.thresholds.n_min == 3
    assert settings.exposure_roles == ["PS", "SS"]


def test_all_six_studies_load_with_one_verified_primary_action():
    studies = load_studies()
    assert len(studies) == 6
    for study in studies:
        assert study.primary_action.verified_on is not None
        assert "primary" in study.event_groups


def minimal_study(**overrides) -> dict:
    study = {
        "study_id": "x",
        "title": "X",
        "definition_status": "draft",
        "drug_group": {"label": "X", "substances": ["X"], "marketed_before_2004": False},
        "event_groups": {"primary": {"label": "E", "pts": ["Nausea "]}},
        "regulatory_actions": [
            {
                "agency": "FDA",
                "date": "2020-01-01",
                "type": "DSC",
                "title": "t",
                "primary": True,
                "verified_on": "2026-10-31",
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
