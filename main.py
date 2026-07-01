from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import googlemaps
import os
import re
from dotenv import load_dotenv

from database import engine, SessionLocal, Base
from models import PisoDB, SitioIntereDB, DistanciaDB

load_dotenv()
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

Base.metadata.create_all(bind=engine)

app = FastAPI()

class PisoCreate(BaseModel):
    precio: float
    metros: float
    habitaciones: int
    direccion: str
    link: Optional[str] = None
    notas: Optional[str] = None

class SitioInteresCreate(BaseModel):
    nombre: str
    direccion: str

class Pesos(BaseModel):
    precio: float = 40
    metros: float = 30
    habitaciones: float = 10
    ubicacion: float = 20

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def texto_a_minutos(texto: str) -> int:
    horas = re.search(r'(\d+)\s*hora', texto)
    minutos = re.search(r'(\d+)\s*min', texto)
    total = 0
    if horas:
        total += int(horas.group(1)) * 60
    if minutos:
        total += int(minutos.group(1))
    return total if total > 0 else 999

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

@app.post("/pisos/{piso_id}/sitios")
def crear_sitio(piso_id: int, sitio: SitioInteresCreate, db: Session = Depends(get_db)):
    piso = db.query(PisoDB).filter(PisoDB.id == piso_id).first()
    if piso is None:
        return {"error": "Piso no encontrado"}
    nuevo_sitio = SitioIntereDB(**sitio.dict(), piso_id=piso_id)
    db.add(nuevo_sitio)
    db.commit()
    db.refresh(nuevo_sitio)
    return nuevo_sitio

@app.get("/pisos/{piso_id}/sitios")
def listar_sitios(piso_id: int, db: Session = Depends(get_db)):
    piso = db.query(PisoDB).filter(PisoDB.id == piso_id).first()
    if piso is None:
        return {"error": "Piso no encontrado"}
    return piso.sitios

@app.delete("/pisos/{piso_id}/sitios/{sitio_id}")
def borrar_sitio(piso_id: int, sitio_id: int, db: Session = Depends(get_db)):
    sitio = db.query(SitioIntereDB).filter(
        SitioIntereDB.id == sitio_id,
        SitioIntereDB.piso_id == piso_id
    ).first()
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

    sitios = piso.sitios
    if not sitios:
        return {"error": "Este piso no tiene sitios de interés definidos"}

    modos = {
        "driving": "Coche",
        "transit": "Transporte público",
        "walking": "A pie",
        "bicycling": "Bicicleta"
    }

    resultados = []
    for sitio in sitios:
        db.query(DistanciaDB).filter(DistanciaDB.sitio_id == sitio.id).delete()
        db.commit()

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
                duracion_texto = elemento["duration"]["text"]
                minutos = texto_a_minutos(duracion_texto)

                nueva_distancia = DistanciaDB(
                    sitio_id=sitio.id,
                    modo=modo,
                    distancia_texto=elemento["distance"]["text"],
                    duracion_texto=duracion_texto,
                    duracion_minutos=minutos
                )
                db.add(nueva_distancia)

                tiempos[etiqueta] = {
                    "distancia": elemento["distance"]["text"],
                    "duracion": duracion_texto
                }
            else:
                tiempos[etiqueta] = {
                    "distancia": "No disponible",
                    "duracion": "No disponible"
                }

        db.commit()
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

    tiempos_medios = []
    for piso in pisos:
        minutos_por_piso = []
        for sitio in piso.sitios:
            distancia_transit = db.query(DistanciaDB).filter(
                DistanciaDB.sitio_id == sitio.id,
                DistanciaDB.modo == "transit"
            ).first()
            if distancia_transit:
                minutos_por_piso.append(distancia_transit.duracion_minutos)
        tiempo_medio = sum(minutos_por_piso) / len(minutos_por_piso) if minutos_por_piso else 999
        tiempos_medios.append(tiempo_medio)

    resultados = []
    for i, piso in enumerate(pisos):
        score_precio = normalizar_invertido(piso.precio, min(precios), max(precios))
        score_metros = normalizar(piso.metros, min(metros), max(metros))
        score_hab = normalizar(piso.habitaciones, min(habitaciones), max(habitaciones))
        score_ubicacion = normalizar_invertido(tiempos_medios[i], min(tiempos_medios), max(tiempos_medios))

        puntuacion = (
            score_precio * pesos.precio +
            score_metros * pesos.metros +
            score_hab * pesos.habitaciones +
            score_ubicacion * pesos.ubicacion
        ) / 100

        resultados.append({
            "id": piso.id,
            "direccion": piso.direccion,
            "precio": piso.precio,
            "metros": piso.metros,
            "habitaciones": piso.habitaciones,
            "tiempo_medio_transporte": f"{int(tiempos_medios[i])} min" if tiempos_medios[i] != 999 else "Sin calcular",
            "puntuacion": round(puntuacion, 1)
        })

    resultados.sort(key=lambda x: x["puntuacion"], reverse=True)
    return resultados
