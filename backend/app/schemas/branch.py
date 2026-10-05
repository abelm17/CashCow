from pydantic import BaseModel, ConfigDict, Field


class BranchBase(BaseModel):
    name: str= Field(min_length=5, max_length=40)
    location_region: str= Field(min_length=2, max_length=30)
    capacity: int
    supervisor_id: int


class BranchRead(BranchBase):
    id: int
    model_config= ConfigDict(from_attributes= True)

class BranchUpdate(BaseModel):
    name: str | None= Field(default= None, min_length=5, max_length=40)
    location_region: str | None= Field(default= None, min_length=2, max_length=30)
    capacity: int | None= None
    supervisor_id: int | None= None

class BranchCreate(BranchBase):
    """ Shape of base model """
    pass


class MaintenanceFlags(BaseModel):
    branch_id: int
    branch_name: str
    total_branches: int
    maintenance_count: int
    maintenance_percentage: float
