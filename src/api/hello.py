from fastapi import FastAPI
from routers import health
from routers import shopping

app = FastAPI(title = "¡Hola, mundo! 🌎",
              description = "API que devuelve un '¡Hola, mundo!'",
              version = "0.1")

app.include_router(health.router)
app.include_router(shopping.router)

@app.get("/")
def hello():
    '''
    Devuelve el mensaje "Hello, world!"
    '''

    response = {"response": "Hello, world!"}

    return response