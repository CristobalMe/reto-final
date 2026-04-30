from fastapi import APIRouter
from schemas.schemas_shopping import CartItem

router = APIRouter(tags = ["Shopping cart"])

shopping = []

@router.get("/shopping-cart")
def shopping_cart():
    '''
    Devuelve la lista de compras.
    '''

    response = {"items": shopping}
    
    return response

@router.get("/shopping-cart/{item_id}")
def query_shopping_cart(item_id: int):
    '''
    Devuelve un elemento de la lista de compras.

    Argumentos
    ----------
    item_id: int
        Posición del elemento en la lista de compras.
    '''

    ## Generamos una respuesta genérica en caso
    ## de que no sea posible acceder al elemento
    response = {"response": f"!El item con id {item_id} no existe en la lista de compras!"}

    ## Comprobamos que el id esté dentro de la lista
    valid = 0 <= item_id < len(shopping)

    ## Buscamos y devolvemos el item
    if valid:
        response = {"response": [shopping[item_id]]}

    return response

@router.post("/add-to-cart")
def add_to_cart(cart_item: CartItem):
    '''
    Añade un item a la lista de compras.

    Argumentos
    ----------
    cart_item: CartItem
        Elemento añadido a la lista.
    '''

    ## Añadimos el elemento item del
    ## objeto CartItem a la lista de compras
    shopping.append(cart_item.item)

    ## Generamos un objeto de respuesta
    response = {"response": f"¡Item {cart_item.item} añadido!"}

    return response