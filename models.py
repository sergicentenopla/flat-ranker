from sqlalchemy import Column, Integer, Float, String
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
