from dataclasses import dataclass


@dataclass
class ReturnData:
    return_date: str
    order_number: str
    pickup_location: str
    item_title: str
