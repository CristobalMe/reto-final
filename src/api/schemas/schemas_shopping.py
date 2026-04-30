from pydantic import BaseModel

class CartItem(BaseModel):
    item: str