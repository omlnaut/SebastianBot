from pydantic import BaseModel, Field


class ReturnData(BaseModel):
    return_date: str = Field(
        description="The date until the return is due. If present, include day month and year."
    )
    order_number: str = Field(description="The order number associated with the return")
    pickup_location: str = Field(
        description="Location where to drop of the return and if i need a printer myself"
    )
    item_title: str = Field(
        description="The title of the item being returned. Might be truncated."
    )
