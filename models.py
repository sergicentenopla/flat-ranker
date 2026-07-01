from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class PisoDB(Base):
    __tablename__ = "pisos"

    id = Column(Integer, primary_key=True, index=True)
    precio = Column(Float)
    metros = Column(Float)
    habitaciones = Column(Integer)
    direccion = Column(String)
    link = Column(String, nullable=True)
    notas = Column(String, nullable=True)

    sitios = relationship("SitioIntereDB", back_populates="piso", cascade="all, delete")

class SitioIntereDB(Base):
    __tablename__ = "sitios_interes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    direccion = Column(String)
    piso_id = Column(Integer, ForeignKey("pisos.id"))

    piso = relationship("PisoDB", back_populates="sitios")
    distancias = relationship("DistanciaDB", back_populates="sitio", cascade="all, delete")

class DistanciaDB(Base):
    __tablename__ = "distancias"

    id = Column(Integer, primary_key=True, index=True)
    sitio_id = Column(Integer, ForeignKey("sitios_interes.id"))
    modo = Column(String)
    distancia_texto = Column(String)
    duracion_texto = Column(String)
    duracion_minutos = Column(Integer)

    sitio = relationship("SitioIntereDB", back_populates="distancias")
