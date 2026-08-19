from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from scripts.models.common.cat import Cat
<<<<<<< HEAD
=======
from scripts.models.common.gather_cat import GatherCat
>>>>>>> clangen-megamerge
from scripts.models.common.relationship_status import RelationshipStatus


class RelationshipConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")
<<<<<<< HEAD
    cats_from: List[Cat] = Field(
        ...,
        description="The cat from whom the relationship originates.",
    )
    cats_to: List[Cat] = Field(
=======
    cats_from: List[GatherCat] = Field(
        ...,
        description="The cat from whom the relationship originates.",
    )
    cats_to: List[GatherCat] = Field(
>>>>>>> clangen-megamerge
        ...,
        description="The target of the relationship.",
    )
    mutual: bool = Field(
        ...,
        description="Controls if the relationship is required in both directions",
    )
    constraints: List[RelationshipStatus] = Field(
        ..., description="Controls which relationship constraints are required"
    )
