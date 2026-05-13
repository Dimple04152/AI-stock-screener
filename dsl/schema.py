from pydantic import BaseModel
from typing import List, Optional, Union

class Filter(BaseModel):
    field: str
    operator: str
    value: Union[str, int, float]

class TimeFilter(BaseModel):
    type: str
    value: str

class DSLQuery(BaseModel):
    filters: List[Filter]
    logic: str
    time_filter: Optional[TimeFilter] = None
