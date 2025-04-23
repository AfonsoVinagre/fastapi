from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing  import Annotated
import models 
from database import engine, SessionLocal, Base
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from datetime import time , date, time , timedelta, datetime
from crud import get_user_by_email_or_phone, verify_password, hash_password
import requests



app = FastAPI()
Base.metadata.create_all(bind=engine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite requisições de qualquer origem (use ["http://localhost:19006"] no Expo)
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os headers
)


class PostBase(BaseModel):
    firstname : str
    lastname : str
    email : str
    phone : str
    password : str
    
class PostBarbearia(BaseModel):
    name : str
    email : str
    phone : str
    adress : str
    
class PostBarbeiro(BaseModel):
    barbearia_id: int
    first_name: str  
    last_name: str   
    email: str
    phone: str 

class PostHorario(BaseModel):
    barbeiro_id: int
    dia: str
    hora_inicio: time
    hora_fim: time
    hora_almoco_inicio: time
    hora_almoco_fim: time
    
class PostAgendamento(BaseModel):
    barbeiro_id: int
    user_id: int
    barbearia_adress : str
    latitude: str
    longitude: str
    barbeiro_nome: str
    barbeiro_numero: str
    data_agendamento: str
    hora_inicio: time
    hora_fim: time
    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

db_dependency = Annotated[Session, Depends(get_db)]

def get_lat_lon(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json"}
    headers = {"User-Agent": "MeuApp/1.0 (afonso.c.vinagre@gmail.com)"}  # Use um e-mail válido!

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()

        data = response.json()
        if not data:
            return None, None

        lat = data[0].get("lat")
        lon = data[0].get("lon")
        return lat, lon if lat and lon else (None, None)

    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição para Nominatim: {e}")
        return None, None
def gerar_intervalos(inicio, fim, slots, duracao, barbeiro_id, data,id):
        atual = datetime.combine(data, inicio)
        fim_dt = datetime.combine(data, fim)
        while atual + duracao <= fim_dt:
            slots.append({
                "id": id ,
                "barbeiro_id": barbeiro_id,
                "data": data,
                "hora_inicio": atual.time(),
                "hora_fim": (atual + duracao).time(),
                "cliente_id": None,
                "status": "disponivel"
            })
            id += 1
            atual += duracao
def gerar_slots_disponiveis(horario,barbeiro_id, data, agendamentos_existentes):
    slots = []
    duracao = timedelta(minutes=40)
    id = 0


    gerar_intervalos(horario['hora_inicio'], horario['hora_almoco_inicio'], slots, duracao, barbeiro_id, data, id)
    id += len(slots)
    gerar_intervalos(horario['hora_almoco_fim'], horario['hora_fim'], slots, duracao, barbeiro_id, data, id)
    
    slots_filtrados = []
    for slot in slots:
        conflito = False
        for ag in agendamentos_existentes:
            if (
                slot["hora_inicio"] == ag.hora_inicio and
                slot["hora_fim"] == ag.hora_fim
            ):
                conflito = True
                break
        if not conflito:
            slots_filtrados.append(slot)

    return slots_filtrados
@app.post("/posts/", status_code=status.HTTP_201_CREATED)
async def create_post(post: PostBase, db: db_dependency):
    existing_email = db.query(models.User).filter(models.User.email == post.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email já está em uso")
    
    # Verificar se o número de telefone já existe
    existing_phone = db.query(models.User).filter(models.User.phone == post.phone).first()
    if existing_phone:
        raise HTTPException(status_code=400, detail="Número de telefone já está em uso")
    post.password=hash_password(post.password)
    
    db_post = models.User(**post.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return {"message": "Usuário criado com sucesso", "user_id": db_post.id}
    
    
@app.post("/criar-barbearia", status_code=status.HTTP_201_CREATED)
async def create_barbearia(post: PostBarbearia, db: db_dependency):
    lat, lon = get_lat_lon(post.adress)  

    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="Endereço inválido ou não encontrado")

    db_post = models.Barbearias(
        name=post.name,
        email=post.email,
        phone=post.phone,
        adress=post.adress,
        latitude=str(lat),
        longitude=str(lon)
    )
    
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return {
        "message": "Barbearia criada com sucesso",
        "barbearia_id": db_post.id,
        "latitude": db_post.latitude,
        "longitude": db_post.longitude
    }


@app.post("/criar-barbeiro", status_code=status.HTTP_201_CREATED)
def criar_barbeiro(post: PostBarbeiro, db: db_dependency):
    db_post = models.Barbeiros(**post.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return {"message": "Barbeiro criado com sucesso", "barbeiro_id": db_post.id}

@app.post("/criar-horario", status_code=status.HTTP_201_CREATED)
def criar_horario(post: PostHorario, db: db_dependency):
    db_post = models.Horarios(**post.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return {"message": "Horário criado com sucesso", "horario_id": db_post.id}

@app.post("/agendar", status_code=status.HTTP_201_CREATED)
def agendar(post: PostAgendamento, db: db_dependency):
    db_post = models.Agendamentos(**post.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

@app.get("/login/")
def login(identifier: str, password: str, db: Session = Depends(get_db)):
    user = get_user_by_email_or_phone(db, identifier)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Senha incorreta")

    return {"message": "Login bem-sucedido", "user_id": user.id}

@app.get("/barbearias/")
def get_barbearias(db: Session = Depends(get_db)):
    barbearias = db.query(models.Barbearias).all()
    return barbearias
@app.get("/barbearia/{barbearia_id}")
def get_barbearia(barbearia_id: int, db: Session = Depends(get_db)):
    barbearia = db.query(models.Barbearias).filter(models.Barbearias.id == barbearia_id).first()
    return barbearia
@app.get("/barbeiros/{barbearia_id}")
def get_barbeiros(barbearia_id: int, db: Session = Depends(get_db)):
    barbeiros = db.query(models.Barbeiros).filter(models.Barbeiros.barbearia_id == barbearia_id).all()
    return barbeiros

@app.get("/barbeiro/{barbeiro_id}")
def get_barbeiro(barbeiro_id: int, db: Session = Depends(get_db)):
    barbeiro = db.query(models.Barbeiros).filter(models.Barbeiros.id == barbeiro_id).first()
    if not barbeiro:
        raise HTTPException(status_code=404, detail="Barbeiro não encontrado")
    return barbeiro

@app.get("/barbeiros/{barbeiro_id}/slots")
def get_slots(barbeiro_id: int, data: date, db: Session = Depends(get_db)):
    dia_semana_idx = data.weekday()
    dias_semana = {
        0: "segunda",
        1: "terça",
        2: "quarta",
        3: "quinta",
        4: "sexta",
        5: "sábado",
        6: "domingo"
    }
    dia_semana_nome = dias_semana[dia_semana_idx]
    # 1. Buscar o horário do barbeiro para esse dia
    horario = db.query(models.Horarios).filter(
        models.Horarios.barbeiro_id==barbeiro_id ,
        models.Horarios.dia==dia_semana_nome
    ).first()

    agendamentos= db.query(models.Agendamentos).filter(
        models.Agendamentos.barbeiro_id==barbeiro_id,
        models.Agendamentos.data_agendamento==data
    ).all()
    if not horario:
        return []
    if(data > datetime.now().date()):
        slots= gerar_slots_disponiveis(horario.__dict__,barbeiro_id, data,agendamentos)
    return slots
@app.get("/agendamentos/{user_id}")
def get_agendamentos(user_id: int, db: Session = Depends(get_db)):
    hoje = datetime.now().date()
    agendamentos = db.query(models.Agendamentos).filter(models.Agendamentos.user_id == user_id, models.Agendamentos.data_agendamento >= hoje).all()
    return agendamentos