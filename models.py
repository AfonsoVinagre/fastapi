from sqlalchemy import Boolean, Column, Integer, String, Time, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
    
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String(50))
    lastname = Column(String(50))
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(20), unique=True, index=True)
    password = Column(String(100))

    agendamentos = relationship("Agendamentos", back_populates="user")

class Barbearias(Base):
    __tablename__ = 'barbearias'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    email = Column(String(100), nullable=False)
    phone = Column(String(20))
    adress = Column(String(100))
    latitude = Column(String(50))
    longitude = Column(String(50))
    
    barbeiros = relationship("Barbeiros", back_populates="barbearia")  # Atualizado o nome correto da relação
    __table_args__ = (
        UniqueConstraint('email', 'id', name='ix_barbearia_email_id'),
    )

class Barbeiros(Base):
    __tablename__ = 'barbeiros'
    
    id = Column(Integer, primary_key=True)
    barbearia_id = Column(Integer, ForeignKey('barbearias.id'))
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(100), nullable=False)
    phone = Column(String(20))
    
    barbearia = relationship("Barbearias", back_populates="barbeiros")
    horarios = relationship("Horarios", back_populates="barbeiros")  # Definição da relação com Horarios
    agendamentos = relationship("Agendamentos", back_populates="barbeiro")

    __table_args__ = (
        UniqueConstraint('email', 'barbearia_id', name='ix_barbeiro_email_id'),
    )

class Horarios(Base):
    __tablename__ = "horarios"
    
    id = Column(Integer, primary_key=True, index=True)
    barbeiro_id = Column(Integer, ForeignKey("barbeiros.id"))
    dia = Column(String(50))
    hora_inicio = Column(Time)
    hora_fim = Column(Time)
    hora_almoco_inicio = Column(Time)
    hora_almoco_fim = Column(Time)
    
    barbeiros = relationship("Barbeiros", back_populates="horarios")

class Agendamentos(Base):
    __tablename__ = "agendamentos"
    
    id = Column(Integer, primary_key=True, index=True)
    barbeiro_id = Column(Integer, ForeignKey("barbeiros.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    barbearia_adress = Column(String(100))
    latitude = Column(String(50))
    longitude = Column(String(50))
    barbeiro_nome = Column(String(50))
    barbeiro_numero = Column(String(20))
    data_agendamento = Column(String(50))
    hora_inicio = Column(Time)
    hora_fim = Column(Time)
    
    barbeiro = relationship("Barbeiros", back_populates="agendamentos")
    user = relationship("User", back_populates="agendamentos")