from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import engine, SessionLocal, Base
from models import PisoDB

Base.metadata.create_all(bind=engine)

app = FastAPI()

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
