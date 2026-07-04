from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import googlemaps
import os
import re
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

from database import engine, SessionLocal, Base
from models import PisoDB, SitioIntereDB, DistanciaDB

load_dotenv()
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Modelos Pydantic ──────────────────────────────────────────

class PisoCreate(BaseModel):
    precio: float = Field(gt=0)
    metros: float = Field(gt=0)
    habitaciones: int = Field(gt=0)
    direccion: str
    link: Optional[str] = None
    notas: Optional[str] = None
    planta: Optional[int] =  Field(default=None, ge=0)
    ascensor: Optional[bool] = None
    terraza: Optional[bool] = None
    parking: Optional[bool] = None
    anyo_construccion: Optional[int] = Field(default=None, ge=1800, le=2030)

class SitioInteresCreate(BaseModel):
    nombre: str
    direccion: str
    peso: float = 1.0

class Pesos(BaseModel):
    valor: float = 40.0
    conectividad: float = 40.0
    habitabilidad: float = 20.0

# ── Utilidades ────────────────────────────────────────────────

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

def normalizar(valor, minimo, maximo):
    if maximo == minimo:
        return 100.0
    return (valor - minimo) / (maximo - minimo) * 100

def normalizar_invertido(valor, minimo, maximo):
    if maximo == minimo:
        return 100.0
    return (maximo - valor) / (maximo - minimo) * 100

def calcular_habitabilidad(piso: PisoDB) -> Optional[float]:
    puntos = []
    if piso.ascensor is not None:
        puntos.append(100.0 if piso.ascensor else 0.0)
    if piso.terraza is not None:
        puntos.append(100.0 if piso.terraza else 0.0)
    if piso.parking is not None:
        puntos.append(100.0 if piso.parking else 0.0)
    if piso.planta is not None:
        puntos.append(min(piso.planta * 10, 100.0))
    if piso.anyo_construccion is not None:
        score_anyo = normalizar(piso.anyo_construccion, 1950, 2024)
        puntos.append(score_anyo)
    if not puntos:
        return None
    return sum(puntos) / len(puntos)

def generar_comentarios(piso, tiempo_medio, precio_metro, media_precio_metro, media_metros):
    positivos = []
    negativos = []

    if precio_metro < media_precio_metro * 0.85:
        positivos.append("Good price per m²")
    elif precio_metro > media_precio_metro * 1.15:
        negativos.append("High price for its size")

    if tiempo_medio < 15:
        positivos.append("Excellent location")
    elif tiempo_medio < 30:
        positivos.append("Good location")
    elif tiempo_medio > 45:
        negativos.append("Far from your points of interest")
    elif tiempo_medio > 30:
        negativos.append("Somewhat far from your points of interest")

    if piso.metros > media_metros * 1.15:
        positivos.append("Spacious compared to others")
    elif piso.metros < media_metros * 0.85:
        negativos.append("Small compared to others")

    if piso.terraza:
        positivos.append("Has terrace")
    if piso.parking:
        positivos.append("Includes parking")
    if piso.ascensor is False and piso.planta and piso.planta > 2:
        negativos.append("No elevator on high floor")

    return positivos, negativos

# ── Endpoints: Pisos ──────────────────────────────────────────

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
        return {"error": "Flat not found"}
    return piso

@app.put("/pisos/{piso_id}")
def actualizar_piso(piso_id: int, piso_actualizado: PisoCreate, db: Session = Depends(get_db)):
    piso = db.query(PisoDB).filter(PisoDB.id == piso_id).first()
    if piso is None:
        return {"error": "Flat not found"}
    for campo, valor in piso_actualizado.dict().items():
        setattr(piso, campo, valor)
    db.commit()
    db.refresh(piso)
    return piso

@app.delete("/pisos/{piso_id}")
def borrar_piso(piso_id: int, db: Session = Depends(get_db)):
    piso = db.query(PisoDB).filter(PisoDB.id == piso_id).first()
    if piso is None:
        return {"error": "Flat not found"}
    db.delete(piso)
    db.commit()
    return {"mensaje": f"Flat {piso_id} deleted"}

# ── Endpoints: Sitios de interés ──────────────────────────────

@app.post("/pisos/{piso_id}/sitios")
def crear_sitio(piso_id: int, sitio: SitioInteresCreate, db: Session = Depends(get_db)):
    piso = db.query(PisoDB).filter(PisoDB.id == piso_id).first()
    if piso is None:
        return {"error": "Flat not found"}
    nuevo_sitio = SitioIntereDB(**sitio.dict(), piso_id=piso_id)
    db.add(nuevo_sitio)
    db.commit()
    db.refresh(nuevo_sitio)
    return nuevo_sitio

@app.get("/pisos/{piso_id}/sitios")
def listar_sitios(piso_id: int, db: Session = Depends(get_db)):
    piso = db.query(PisoDB).filter(PisoDB.id == piso_id).first()
    if piso is None:
        return {"error": "Flat not found"}
    return piso.sitios

@app.delete("/pisos/{piso_id}/sitios/{sitio_id}")
def borrar_sitio(piso_id: int, sitio_id: int, db: Session = Depends(get_db)):
    sitio = db.query(SitioIntereDB).filter(
        SitioIntereDB.id == sitio_id,
        SitioIntereDB.piso_id == piso_id
    ).first()
    if sitio is None:
        return {"error": "Point of interest not found"}
    db.delete(sitio)
    db.commit()
    return {"mensaje": f"Point of interest {sitio_id} deleted"}

# ── Endpoints: Distancias ─────────────────────────────────────

@app.get("/pisos/{piso_id}/distancias")
def calcular_distancias(piso_id: int, db: Session = Depends(get_db)):
    piso = db.query(PisoDB).filter(PisoDB.id == piso_id).first()
    if piso is None:
        return {"error": "Flat not found"}

    sitios = piso.sitios
    if not sitios:
        return {"error": "This flat has no points of interest defined"}

    modos = {
        "driving": "Car",
        "transit": "Public transport",
        "walking": "Walking",
        "bicycling": "Bicycle"
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
                    "distancia": "Not available",
                    "duracion": "Not available"
                }

        db.commit()
        resultados.append({"sitio": sitio.nombre, "tiempos": tiempos})

    return {"piso_id": piso_id, "distancias": resultados}

# ── Endpoint: Scoring ─────────────────────────────────────────

@app.post("/scoring")
def calcular_scoring(pesos: Pesos, db: Session = Depends(get_db)):
    pisos = db.query(PisoDB).all()
    if not pisos:
        return {"error": "No flats saved"}

    # Calcular €/m² para todos los pisos
    precios_metro = [p.precio / p.metros for p in pisos]
    metros_lista = [p.metros for p in pisos]

    # Calcular tiempo medio ponderado por POIs para cada piso
    tiempos_medios = []
    for piso in pisos:
        suma_ponderada = 0.0
        suma_pesos = 0.0
        for sitio in piso.sitios:
            distancia = db.query(DistanciaDB).filter(
                DistanciaDB.sitio_id == sitio.id,
                DistanciaDB.modo == "transit"
            ).first()
            if distancia:
                suma_ponderada += distancia.duracion_minutos * sitio.peso
                suma_pesos += sitio.peso
        tiempo_medio = (suma_ponderada / suma_pesos) if suma_pesos > 0 else None
        tiempos_medios.append(tiempo_medio)

    # Calcular habitabilidad para cada piso
    habitabilidades = [calcular_habitabilidad(p) for p in pisos]

    resultados = []
    media_precio_metro = sum(precios_metro) / len(precios_metro)
    media_metros = sum(metros_lista) / len(metros_lista)

    for i, piso in enumerate(pisos):

        # Score Valor (€/m², invertido: menos es mejor)
        score_valor = normalizar_invertido(
            precios_metro[i], min(precios_metro), max(precios_metro)
        )

        # Score Conectividad
        tiempos_validos = [t for t in tiempos_medios if t is not None]
        if tiempos_medios[i] is not None and tiempos_validos:
            score_conectividad = normalizar_invertido(
                tiempos_medios[i], min(tiempos_validos), max(tiempos_validos)
            )
        else:
            score_conectividad = None

        # Score Habitabilidad
        score_habitabilidad = habitabilidades[i]

        # Redistribución automática de pesos si faltan dimensiones
        peso_valor = pesos.valor
        peso_conectividad = pesos.conectividad
        peso_habitabilidad = pesos.habitabilidad

        if score_conectividad is None and score_habitabilidad is None:
            peso_valor = 100.0
            peso_conectividad = 0.0
            peso_habitabilidad = 0.0
        elif score_conectividad is None:
            total = peso_valor + peso_habitabilidad
            peso_valor = (peso_valor / total) * 100
            peso_habitabilidad = (peso_habitabilidad / total) * 100
            peso_conectividad = 0.0
        elif score_habitabilidad is None:
            total = peso_valor + peso_conectividad
            peso_valor = (peso_valor / total) * 100
            peso_conectividad = (peso_conectividad / total) * 100
            peso_habitabilidad = 0.0

        puntuacion = (
            score_valor * peso_valor +
            (score_conectividad or 0) * peso_conectividad +
            (score_habitabilidad or 0) * peso_habitabilidad
        ) / 100

        # Comentarios cualitativos
        tiempo_para_comentarios = tiempos_medios[i] if tiempos_medios[i] is not None else 999
        positivos, negativos = generar_comentarios(
            piso, tiempo_para_comentarios,
            precios_metro[i], media_precio_metro, media_metros
        )


        resultados.append({
            "id": piso.id,
            "direccion": piso.direccion,
            "precio_por_metro": round(precios_metro[i], 2),
            "tiempo_medio_transporte": f"{int(tiempos_medios[i])} min" if tiempos_medios[i] is not None else "Not calculated",
            "puntuacion": round(puntuacion, 1),
            "positivos": positivos,
            "negativos": negativos
        })

    resultados.sort(key=lambda x: x["puntuacion"], reverse=True)
    return resultados
