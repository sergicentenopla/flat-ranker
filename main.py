from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import engine, SessionLocal, Base
from models import PisoDB


import googlemaps
import os
from dotenv import load_dotenv
from models import SitioIntereDB

load_dotenv()
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))


Base.metadata.create_all(bind=engine)

app = FastAPI()

class SitioInteresCreate(BaseModel):
    nombre: str
    direccion: str

class Pesos(BaseModel):
    precio: float = 50
    metros: float = 30
    habitaciones: float = 20

class PisoCreate(BaseModel):
    precio: float
    metros: float
    habitaciones: int
    direccion: str
    link: Optional[str] = None
    notas: Optional[str] = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.post("/pisos")
def crear_piso(piso: PisoCreate, db: Session = Depends(get_db)):
    nuevo_piso = PisoDB(**piso.dict())
    db.add(nuevo_piso)
    db.commit()
    db.refresh(nuevo_piso)
    return nuevo_piso

@app.get("/pisos")
def listar_pisos(db: Session = Depends(get_db)):
    return db.query(PisoDB).all()

@app.get("/pisos/{piso_id}")
def obtener_piso(piso_id: int, db: Session = Depends(get_db)):
    piso = db.query(PisoDB).filter(PisoDB.id == piso_id).first()
    if piso is None:
        return {"error": "Piso no encontrado"}
    return piso

@app.put("/pisos/{piso_id}")
def actualizar_piso(piso_id: int, piso_actualizado: PisoCreate, db: Session = Depends(get_db)):
    piso = db.query(PisoDB).filter(PisoDB.id == piso_id).first()
    if piso is None:
        return {"error": "Piso no encontrado"}
    
    for campo, valor in piso_actualizado.dict().items():
        setattr(piso, campo, valor)
    
    db.commit()
    db.refresh(piso)
    return piso

@app.delete("/pisos/{piso_id}")
def borrar_piso(piso_id: int, db: Session = Depends(get_db)):
    piso = db.query(PisoDB).filter(PisoDB.id == piso_id).first()
    if piso is None:
        return {"error": "Piso no encontrado"}
    
    db.delete(piso)
    db.commit()
    return {"mensaje": f"Piso {piso_id} borrado"}






@app.post("/sitios")
def crear_sitio(sitio: SitioInteresCreate, db: Session = Depends(get_db)):
    nuevo_sitio = SitioIntereDB(**sitio.dict())
    db.add(nuevo_sitio)
    db.commit()
    db.refresh(nuevo_sitio)
    return nuevo_sitio

@app.get("/sitios")
def listar_sitios(db: Session = Depends(get_db)):
    return db.query(SitioIntereDB).all()

@app.delete("/sitios/{sitio_id}")
def borrar_sitio(sitio_id: int, db: Session = Depends(get_db)):
    sitio = db.query(SitioIntereDB).filter(SitioIntereDB.id == sitio_id).first()
    if sitio is None:
        return {"error": "Sitio no encontrado"}
    db.delete(sitio)
    db.commit()
    return {"mensaje": f"Sitio {sitio_id} borrado"}

@app.get("/pisos/{piso_id}/distancias")
def calcular_distancias(piso_id: int, db: Session = Depends(get_db)):
    piso = db.query(PisoDB).filter(PisoDB.id == piso_id).first()
    if piso is None:
        return {"error": "Piso no encontrado"}

    sitios = db.query(SitioIntereDB).all()
    if not sitios:
        return {"error": "No hay sitios de interés definidos"}

    modos = {
        "driving": "Coche",
        "transit": "Transporte público",
        "walking": "A pie",
        "bicycling": "Bicicleta"
    }

    resultados = []
    for sitio in sitios:
        tiempos = {}
        for modo, etiqueta in modos.items():
            resultado = gmaps.distance_matrix(
                origins=piso.direccion,
                destinations=sitio.direccion,
                mode=modo,
                language="es"
            )
            elemento = resultado["rows"][0]["elements"][0]
            if elemento["status"] == "OK":
                tiempos[etiqueta] = {
                    "distancia": elemento["distance"]["text"],
                    "duracion": elemento["duration"]["text"]
                }
            else:
                tiempos[etiqueta] = {
                    "distancia": "No disponible",
                    "duracion": "No disponible"
                }

        resultados.append({
            "sitio": sitio.nombre,
            "tiempos": tiempos
        })

    return {"piso_id": piso_id, "distancias": resultados}



@app.post("/scoring")
def calcular_scoring(pesos: Pesos, db: Session = Depends(get_db)):
    pisos = db.query(PisoDB).all()
    if not pisos:
        return {"error": "No hay pisos guardados"}

    peso_precio = pesos.precio
    peso_metros = pesos.metros
    peso_habitaciones = pesos.habitaciones

    precios = [p.precio for p in pisos]
    metros = [p.metros for p in pisos]
    habitaciones = [p.habitaciones for p in pisos]

    def normalizar(valor, minimo, maximo):
        if maximo == minimo:
            return 100
        return (valor - minimo) / (maximo - minimo) * 100

    def normalizar_invertido(valor, minimo, maximo):
        if maximo == minimo:
            return 100
        return (maximo - valor) / (maximo - minimo) * 100

    resultados = []
    for piso in pisos:
        score_precio = normalizar_invertido(piso.precio, min(precios), max(precios))
        score_metros = normalizar(piso.metros, min(metros), max(metros))
        score_hab = normalizar(piso.habitaciones, min(habitaciones), max(habitaciones))

        puntuacion = (
            score_precio * peso_precio +
            score_metros * peso_metros +
            score_hab * peso_habitaciones
        ) / 100

        resultados.append({
            "id": piso.id,
            "direccion": piso.direccion,
            "precio": piso.precio,
            "metros": piso.metros,
            "habitaciones": piso.habitaciones,
            "puntuacion": round(puntuacion, 1)
        })

    resultados.sort(key=lambda x: x["puntuacion"], reverse=True)
    return resultados

