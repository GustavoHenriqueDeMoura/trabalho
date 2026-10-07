import os
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, select, String, Integer, DateTime, ForeignKey
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship
 
 
# ---------- Modelos ----------
class Base(DeclarativeBase):
    pass
 
 
class Sessao(Base):
    __tablename__ = "Sessao"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome_campanha: Mapped[str] = mapped_column(String(250))
    data_dia: Mapped[datetime] = mapped_column(DateTime)
    duracao_minutos: Mapped[int] = mapped_column(Integer)
 
    players: Mapped[List["Player"]] = relationship(back_populates="sessao")
 
 
class Player(Base):
    __tablename__ = "Player"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(250))
    telefone: Mapped[str] = mapped_column(String(250))
    personagem: Mapped[str] = mapped_column(String(250))
    sessao_id: Mapped[Optional[int]] = mapped_column(ForeignKey("Sessao.id"))
 
    sessao: Mapped[Optional["Sessao"]] = relationship(back_populates="players")
 
 
# ---------- Conexão (dados sensíveis vêm do .env) ----------
load_dotenv()
 
BANCOS = {
    "1": ("SQLite", "SQLITE_URL"),
    "2": ("MySQL", "MYSQL_URL"),
}
 
 
def conectar(permitir_cancelar: bool = False):
    """Pergunta qual banco usar e devolve (nome, engine).
    Devolve None se o usuário cancelar (só quando permitir_cancelar=True)."""
    while True:
        print("\n=== ESCOLHA O BANCO DE DADOS ===")
        for chave, (nome, _) in BANCOS.items():
            print(f"{chave} - {nome}")
        if permitir_cancelar:
            print("0 - Cancelar (manter o banco atual)")
 
        escolha = input("Escolha: ").strip()
        if permitir_cancelar and escolha == "0":
            return None
        if escolha not in BANCOS:
            print("Opção inválida.")
            continue
 
        nome, variavel = BANCOS[escolha]
        url = os.getenv(variavel)
        if not url:
            print(f"A variável {variavel} não foi encontrada no .env.")
            continue
 
        try:
            engine = create_engine(url)
            Base.metadata.create_all(engine)  # testa a conexão e cria as tabelas
        except SQLAlchemyError as erro:
            print(f"Não foi possível conectar ao {nome}: {erro}")
            continue
 
        print(f"Conectado ao {nome}.")
        return nome, engine
 
 
# ---------- Entrada de dados ----------
def ler_int(msg: str) -> int:
    while True:
        try:
            return int(input(msg))
        except ValueError:
            print("Digite um número válido.")
 
 
def ler_data(msg: str) -> datetime:
    while True:
        try:
            return datetime.strptime(input(msg), "%d/%m/%Y %H:%M")
        except ValueError:
            print("Formato inválido. Use Dia/Mês/Ano Hora:Minuto")
 
 
# ---------- Ações do menu ----------
def cadastrar_sessao(db: Session):
    sessao = Sessao(
        nome_campanha=input("Nome da campanha: "),
        data_dia=ler_data("Data e hora (DD/MM/AAAA HH:MM): "),
        duracao_minutos=ler_int("Duração em minutos: "),
    )
    db.add(sessao)
    db.commit()
    print(f"Sessão criada com id {sessao.id}.")
 

def cadastrar_player(db: Session):
    player = Player(
        nome=input("Nome: "),
        telefone=input("Telefone: "),
        personagem=input("Personagem: "),
    )
    db.add(player)
    db.commit()
    print(f"Player criado com id {player.id}.")
 
 
def listar_sessoes(db: Session):
    sessoes = db.scalars(select(Sessao)).all()
    if not sessoes:
        print("Nenhuma sessão cadastrada.")
        return
    for s in sessoes:
        print(f"\n[{s.id}] {s.nome_campanha} - {s.data_dia:%d/%m/%Y %H:%M} ({s.duracao_minutos} min)")
        if s.players:
            for p in s.players:
                print(f"    - {p.nome} ({p.personagem})")
        else:
            print("    (sem players)")
 
 
def listar_players(db: Session):
    players = db.scalars(select(Player)).all()
    if not players:
        print("Nenhum player cadastrado.")
        return
    for p in players:
        sessao = p.sessao.nome_campanha if p.sessao else "sem sessão"
        print(f"[{p.id}] {p.nome} - {p.personagem} - {p.telefone} | {sessao}")
 
 
def colocar_player_na_sessao(db: Session):
    player = db.get(Player, ler_int("ID do player: "))
    sessao = db.get(Sessao, ler_int("ID da sessão: "))
    if player is None or sessao is None:
        print("Player ou sessão não encontrado.")
        return
    player.sessao = sessao
    db.commit()
    print(f"{player.nome} agora está em '{sessao.nome_campanha}'.")
 
 
def excluir_player(db: Session):
    player = db.get(Player, ler_int("ID do player: "))
    if player is None:
        print("Player não encontrado.")
        return
    db.delete(player)
    db.commit()
    print("Player excluído.")

def excluir_sessao(db: Session):
    sessao = db.get(Sessao, ler_int("ID Campanha: "))
    if sessao is None:
        print("Campanha não encontrado.")
        return
    db.delete(sessao)
    db.commit()
    print("Campanha ecluida excluído.")
 
 
# ---------- Menu principal ----------
OPCOES = {
    "1": ("Cadastrar sessão", cadastrar_sessao),
    "2": ("Cadastrar player", cadastrar_player),
    "3": ("Listar sessões", listar_sessoes),
    "4": ("Listar players", listar_players),
    "5": ("Colocar player em uma sessão", colocar_player_na_sessao),
    "6": ("Excluir player", excluir_player),
    "7": ("Excluir campanha", excluir_sessao),
}
 
 
def menu():
    nome_banco, engine = conectar()
    db = Session(engine)
    try:
        while True:
            print(f"\n=== MENU (banco atual: {nome_banco}) ===")
            for chave, (texto, _) in OPCOES.items():
                print(f"{chave} - {texto}")
            print("8 - Trocar de banco de dados")
            print("0 - Sair")
 
            escolha = input("Escolha: ").strip()
            if escolha == "0":
                print("Até mais!")
                break
            if escolha == "8":
                nova = conectar(permitir_cancelar=True)
                if nova is not None:
                    db.close()
                    nome_banco, engine = nova
                    db = Session(engine)
            elif escolha in OPCOES:
                try:
                    OPCOES[escolha][1](db)
                except SQLAlchemyError as erro:
                    db.rollback()
                    print(f"Erro no banco de dados: {erro}")
            else:
                print("Opção inválida.")
    finally:
        db.close()
 
 
if __name__ == "__main__":
    menu()
