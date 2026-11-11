"""Load and validate the YAML configuration (settings + one file per case study).

Validation happens once, when the files are loaded. A typo in a study file
(missing primary action, unknown agency, empty PT list) stops the pipeline
with a clear message instead of producing silently wrong results.
"""

import datetime as dt
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"

QUARTER_PATTERN = re.compile(r"^\d{4}Q[1-4]$")


# ---------- settings.yaml ----------


class Quarters(BaseModel):
    start: str
    end: str  # "latest" or e.g. "2026Q3"

    @field_validator("start", "end")
    @classmethod
    def check_quarter(cls, value: str) -> str:
        if value != "latest" and not QUARTER_PATTERN.match(value):
            raise ValueError(f"quarter must look like 2004Q1 or 'latest', got {value!r}")
        return value


class Thresholds(BaseModel):
    prr_min: float
    chi2_min: float
    chi2_use_yates: bool
    n_min: int
    ror_lower_min: float


class Llm(BaseModel):
    model: str | None
    temperature: float
    max_tokens: int


class Author(BaseModel):
    name: str
    linkedin: str
    cv: str


class Headline(BaseModel):
    """Pre-registered rule for the one-sentence result on the home page."""

    criterion: Literal["evans", "ror"]
    drug_key: str  # "class" = the whole drug group of a study
    event_key: str
    first_signal_rule: Literal["first_crossing", "sustained"]
    median_min_studies: int = Field(ge=1)  # fewer uncensored studies -> no median


class Settings(BaseModel):
    quarters: Quarters
    thresholds: Thresholds
    exposure_roles: list[Literal["PS", "SS", "C", "I"]]
    post_action_quarters: int
    headline: Headline
    site: dict[str, str]
    llm: Llm
    author: Author


# ---------- config/studies/<study_id>.yaml ----------


class DrugGroup(BaseModel):
    label: str
    substances: list[str] = Field(min_length=1)
    marketed_before_2004: bool  # True -> early signals may be left-censored
    # First US approval per substance (Drugs@FDA, earliest original NDA approval).
    approval_dates: dict[str, dt.date]

    @model_validator(mode="after")
    def one_approval_date_per_substance(self) -> "DrugGroup":
        if set(self.approval_dates) != set(self.substances):
            raise ValueError(
                f"approval_dates must list exactly the substances {self.substances}, "
                f"got {sorted(self.approval_dates)}"
            )
        return self


class EventGroup(BaseModel):
    label: str
    pts: list[str] = Field(min_length=1)  # MedDRA Preferred Terms, upper case

    @field_validator("pts")
    @classmethod
    def upper_case_pts(cls, pts: list[str]) -> list[str]:
        return [pt.strip().upper() for pt in pts]


class RegulatoryAction(BaseModel):
    # MAH = label change made by the marketing authorisation holder
    agency: Literal["FDA", "EMA", "MHRA", "MAH"]
    # Decision date printed in the source (for a PRAC meeting: its last day).
    # Lead time is always computed from this date.
    date: dt.date
    date_precision: Literal["day", "month"] = "day"
    published_on: dt.date | None = None  # when the source came out later than `date`
    type: str
    title: str
    url: str | None = None
    archive_url: str | None = None  # permanent copy, e.g. in the Wayback Machine
    quote: str | None = None  # verbatim text from the source that shows the date
    primary: bool = False
    # None = the date still has to be checked in an official document
    verified_on: dt.date | None = None
    note: str | None = None


class Study(BaseModel):
    study_id: str
    title: str
    # frozen = PT lists locked before any results are computed (pre-registration)
    definition_status: Literal["draft", "frozen"]
    drug_group: DrugGroup
    event_groups: dict[str, EventGroup]
    regulatory_actions: list[RegulatoryAction]
    caveats: list[str] = []

    @model_validator(mode="after")
    def check_study(self) -> "Study":
        if "primary" not in self.event_groups:
            raise ValueError(f"{self.study_id}: event_groups must contain 'primary'")
        primaries = [a for a in self.regulatory_actions if a.primary]
        if len(primaries) != 1:
            raise ValueError(f"{self.study_id}: exactly one regulatory action must be primary")
        primary = primaries[0]
        if primary.agency not in ("FDA", "EMA"):
            raise ValueError(f"{self.study_id}: the primary action must be by FDA or EMA")
        if primary.date_precision != "day" or primary.verified_on is None:
            raise ValueError(f"{self.study_id}: the primary action needs a verified exact date")
        if not primary.quote or not primary.archive_url:
            raise ValueError(
                f"{self.study_id}: the primary action needs a quote and an archive_url"
            )
        return self

    @property
    def primary_action(self) -> RegulatoryAction:
        return next(a for a in self.regulatory_actions if a.primary)


# ---------- loaders ----------


def _read_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_settings(config_dir: Path = CONFIG_DIR) -> Settings:
    return Settings.model_validate(_read_yaml(config_dir / "settings.yaml"))


def load_studies(config_dir: Path = CONFIG_DIR) -> list[Study]:
    studies = []
    for path in sorted((config_dir / "studies").glob("*.yaml")):
        study = Study.model_validate(_read_yaml(path))
        if study.study_id != path.stem:
            raise ValueError(f"{path.name}: study_id {study.study_id!r} must match the file name")
        studies.append(study)
    return studies
