from enum import Enum
from typing import Union, Annotated

from pydantic import StringConstraints, RootModel


class GatherCatEnum(Enum):
    m_c = "m_c"
    not_m_c = "-m_c"
    r_c = "r_c"
    not_r_c = "-r_c"
    p_l = "p_l"
    not_p_l = "-p_l"
    s_c = "s_c"
    not_s_c = "-s_c"
<<<<<<< HEAD
    app1 = "app1"
    not_app1 = "-app1"
    app2 = "app2"
    not_app2 = "-app2"
    app3 = "app3"
    not_app3 = "-app3"
    app4 = "app4"
    not_app4 = "-app4"
    app5 = "app5"
    not_app5 = "-app5"
    app6 = "app6"
    not_app6 = "-app6"
=======
>>>>>>> clangen-megamerge
    clan = "clan"
    not_clan = "-clan"
    some_clan = "some_clan"
    not_some_clan = "-some_clan"
    patrol = "patrol"
    not_patrol = "-patrol"
    multi = "multi"
    not_multi = "-multi"
    high_lawful = "high_lawful"
    not_high_lawful = "-high_lawful"
    low_lawful = "low_lawful"
    not_low_lawful = "-low_lawful"
    high_social = "high_social"
    not_high_social = "-high_social"
    low_social = "low_social"
    not_low_social = "-low_social"
    high_stable = "high_stable"
    not_high_stable = "-high_stable"
    low_stable = "low_stable"
    not_low_stable = "-low_stable"
    high_aggress = "high_aggress"
    not_high_aggress = "-high_aggress"
    low_aggress = "low_aggress"
    not_low_aggress = "-low_aggress"
<<<<<<< HEAD
=======
    patrol_cats = "patrol_cats"
    not_patrol_cats = "-patrol_cats"
    apprentice = "apprentice"
    not_apprentice = "-apprentice"
    medicine_cat_apprentice = "medicine cat apprentice"
    not_medicine_cat_apprentice = "-medicine cat apprentice"
    warrior = "warrior"
    not_warrior = "-warrior"
    medicine_cat = "medicine cat"
    not_medicine_cat = "-medicine cat"
    deputy = "deputy"
    not_deputy = "-deputy"
    leader = "leader"
    not_leader = "-leader"
>>>>>>> clangen-megamerge


class GatherCat(RootModel):
    root: Union[
<<<<<<< HEAD
        GatherCatEnum, Annotated[str, StringConstraints(pattern=r"^-?n_c:[0-9]+$")]
=======
        GatherCatEnum,
        Annotated[str, StringConstraints(pattern=r"^-?n_c:[0-9]+$")],
        Annotated[str, StringConstraints(pattern=r"^-?(n_c|r_c|s_c)[0-9]+$")],
>>>>>>> clangen-megamerge
    ]
