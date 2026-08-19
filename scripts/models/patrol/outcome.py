from __future__ import annotations

<<<<<<< HEAD
from typing import Annotated, Dict, List, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field
from pydantic_core import MISSING
from scripts.models.common.gather_cat import GatherCat
from scripts.models.common.herb import Herb
from scripts.models.common.min_max_status import MinMaxStatusDictKey
from scripts.models.common.new_cat import NewCat
from scripts.models.common.future_event import FutureEvent
from scripts.models.common.relationship_status import RelationshipStatus
from scripts.models.common.skill import Skill
from scripts.models.common.trait import Trait
from scripts.models.patrol.can_have_status import CanHaveStat
from scripts.models.patrol.history_text import HistoryText
from scripts.models.patrol.injury_item import InjuryItem
from scripts.models.patrol.leader_lives_lost import LeaderLivesLost
from scripts.models.patrol.patrol_herb import PatrolHerb
from scripts.models.patrol.prey import Prey
from scripts.models.common.relationship import Relationship
=======
from typing import Dict, List, Tuple, Union, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, RootModel
from pydantic_core import MISSING
from scripts.models.common.gather_cat import GatherCat
from scripts.models.common.location import Location
from scripts.models.common.min_max_status import MinMaxStatusDictKey
from scripts.models.common.future_event import FutureEvent
from scripts.models.common.season import Season
from scripts.models.common.tag import Tag
from scripts.models.patrol.condition import Condition
from scripts.models.patrol.death import Death
from scripts.models.patrol.involved_cats import InvolvedCatsPatrolEvent
from scripts.models.patrol.join import Join
from scripts.models.patrol.supply import Supply
from scripts.models.text_pool_event.relationship_change_dict import RelationshipChange
from scripts.models.text_pool_event.relationship_constraint_dict import (
    RelationshipConstraint,
)


class RequiredRepution(BaseModel):
    outsider: list[Literal["welcoming", "neutral", "hostile"]] | MISSING = MISSING
    other_clan: list[Literal["ally", "neutral", "hostile"]] | MISSING = MISSING
>>>>>>> clangen-megamerge


class Outcome(BaseModel):
    model_config = ConfigDict(extra="forbid")
<<<<<<< HEAD
    text: str = Field(..., description="Displayed outcome text.")
    frequency: Annotated[
        int,
        Field(
            description="Controls how common an outcome is.",
            json_schema_extra={
                "default": 4
            },  # Necessary so that JSON Schema still shows a default without making the field optional
        ),
    ]
    exp: int = Field(..., description="Base exp gain.")
    stat_skill: Union[List[Skill], MISSING] = Field(
        MISSING,
        description="Makes this a stat outcome which can occur if a stat cat can be found.",
    )
    stat_trait: Union[List[Trait], MISSING] = Field(
        MISSING,
        description="Makes this a stat outcome which can occur if a stat cat can be found.",
    )
    can_have_stat: Union[List[CanHaveStat], MISSING] = Field(
        MISSING,
        description="Overrides default behavior or adds additional requirements for stat_cat picking.",
    )
    prey: Union[List[Prey], MISSING] = Field(
        MISSING, description="Indicates how much prey each cat brings back."
    )
    herbs: Union[List[Union[Herb, PatrolHerb]], MISSING] = Field(
        MISSING, description="Indicates which herbs will be given."
    )
    lost_cats: Union[List[GatherCat], MISSING] = Field(
        MISSING, description="Indicates which cats will become lost."
    )
    dead_cats: Union[List[Union[GatherCat, LeaderLivesLost]], MISSING] = Field(
        MISSING, description="Indicates which cats will die."
    )
    injury: Union[List[InjuryItem], MISSING] = Field(
        MISSING, description="Indicates which cats get injured and how."
    )
    min_max_status: Union[Dict[MinMaxStatusDictKey, Tuple[int, int]], MISSING] = Field(
        MISSING,
        description="Allows specification of the minimum and maximum number of specific types of cats that are allowed on the patrol.",
    )
    history_text: Union[HistoryText, MISSING] = Field(
        MISSING, description="Controls the history-text for scars and death."
    )
    relationships: Union[List[Relationship], MISSING] = Field(
        MISSING, description="Indicates effect on cat relationships."
    )
    relationship_constraint: Union[List[RelationshipStatus], MISSING] = Field(
        MISSING,
        description="Dictates what relationships m_c must have towards r_c. Do not use this section if there is no r_c in the event.",
    )
    new_cat: Union[List[NewCat], MISSING] = Field(
        MISSING,
        description="Adds new cat(s), either joining the clan or as outside cats. The {index} value corresponds to their index value on this list (e.g. n_c:0 refers to the first cat in this list).",
    )
    art: Union[str, MISSING] = Field(
        MISSING,
        description="Name of outcome-specific art, without file extension (no .png). If no art is specified, the intro art will be used.",
    )
    art_clean: Union[str, MISSING] = Field(
        MISSING,
        description="Name of non-gore outcome-specific art, without file extension (no .png). Adding a clean version of the art marks the normal version as containing gore.",
    )
    outsider_rep: Union[int, MISSING] = Field(
        MISSING,
        description="How much outsider reputation will change. Can be positive or negative.",
    )
    other_clan_rep: Union[int, MISSING] = Field(
        MISSING,
        description="How much reputation with other Clan will change. Can be positive or negative.",
    )
    future_event: Union[FutureEvent, MISSING] = MISSING
=======
    frequency: int = Field(
        ...,
        description="Controls how common an outcome is. 4 is the most common, 1 is the least.",
        json_schema_extra={
            "default": 4
        },  # Necessary so that JSON Schema still shows a default without making the field optional
    )
    location: Union[Location, MISSING] = Field(
        MISSING,
        description="Constrains the event to only occur if a player chooses a specific biome.",
    )
    season: Union[List[Season], MISSING] = Field(
        MISSING,
        description="Constrains the event to only occur once the Clan is in a specific season.",
    )
    tags: Union[
        List[Tag],
        MISSING,
    ] = Field(MISSING, description="Used for some filtering purposes")

    outcome_art: Union[str, MISSING] = Field(
        MISSING,
        description="The name of displayed patrol art file, without any file extension (no .png).",
    )
    outcome_art_clean: Union[str, MISSING] = Field(
        MISSING,
        description='If patrol_art contains gore, this line can hold a clean version. The existence of a non-empty string in this parameter marks the patrol art in "patrol_art" as explicit.',
    )
    strings: List[str] = Field(
        ..., description="List of the text that will be displayed in-game as events."
    )
    required_cat_types: Union[
        Dict[MinMaxStatusDictKey, Tuple[int, int]], MISSING
    ] = Field(
        MISSING,
        description="Allows specification of the minimum and maximum number of specific types of cats that are allowed on the patrol.",
    )
    involved_cats: Union[InvolvedCatsPatrolEvent, MISSING] = Field(
        MISSING,
        description="Used to add constraints for the various involved cats.",
    )
    required_reputation: Union[RequiredRepution, MISSING] = Field(
        MISSING,
        description="Constrains the event to only occur if the player clan has the required reputation",
    )
    relationship_constraint: Union[List[RelationshipConstraint], MISSING] = Field(
        MISSING,
        description="Used to require specific relationships between the cats",
    )
    exp_gained: int = Field(
        ...,
        description="The amount of exp cats receive (sorta). The exact amount also depends on the number of cats and current EXP levels, but in general, a higher number here means more exp. If exp is 0, no exp will be given",
    )
    reputation_changes: Union[
        dict[Literal["outsider", "other_clan"], int], MISSING
    ] = MISSING
    relationship_changes: Union[List[RelationshipChange], MISSING] = Field(
        MISSING,
        description="Used to change specific relationships between the cats",
    )
    supply: Union[List[Supply], MISSING] = Field(
        MISSING,
        description="Indicates changes to the supply of the Clan. Each supply change block is a new change",
    )
    death: Union[List[Death], MISSING] = Field(
        MISSING,
        description='Indicate which cats should die as a result of this outcome. You can specify different "types" of death as separate blocks',
    )
    condition: Union[List[Condition], MISSING] = Field(
        MISSING,
        description="Indicate which cats should receive conditions and what conditions they receive. You can add multiple condition blocks",
    )
    lost: Union[List[Dict[Literal["cats"], list[GatherCat]]], MISSING] = Field(
        MISSING,
        description="Indicate which cats should be lost from their Clan. You can add multiple lost blocks",
    )
    join: Union[List[Join], MISSING] = Field(
        MISSING,
        description="Indicate which cats will join the player Clan. You can add multiple join blocks",
    )
    future_event: Union[List[FutureEvent], MISSING] = Field(
        MISSING, description="Schedules another event to happen in the future."
    )
>>>>>>> clangen-megamerge
