from pydantic import BaseModel, Field


class UnitsProgressBody(BaseModel):
    units_separated: int = Field(..., ge=0, description="Total acumulado de unidades separadas na OS atual.")
