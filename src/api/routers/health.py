from fastapi import APIRouter

router = APIRouter(tags = ["Health"])

@router.get("/health")
def server_status():
    '''
    Verifica el estatus del servidor
    '''

    response = {"status": "Servicio levantado y corriendo."}
    
    return response