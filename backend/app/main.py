from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, Field, Session, create_engine, select
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

app = FastAPI(title="QuickLiqi API")

class Deal(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    address: str
    price: float

@app.on_event("startup")
def on_startup() -> None:
    SQLModel.metadata.create_all(engine)

# Dependency
def get_session() -> Session:
    with Session(engine) as session:
        yield session

@app.get("/api/deals")
def read_deals(session: Session = Depends(get_session)):
    return session.exec(select(Deal)).all()

@app.post("/api/deals")
def create_deal(deal: Deal, session: Session = Depends(get_session)):
    session.add(deal)
    session.commit()
    session.refresh(deal)
    return deal
