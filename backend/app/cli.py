import argparse
from getpass import getpass

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.api.auth import passwords
from app.db.models import Family, User, Membership, Session as LoginSession
from app.db.unit_of_work import engine


def provision(family_name, name, email, password, family_id=None):
    email = email.strip().lower()
    if len(password) < 12:
        raise ValueError("Use uma senha com pelo menos 12 caracteres.")
    with Session(engine) as db, db.begin():
        if db.scalar(select(User).where(User.email == email)):
            raise ValueError("Email já cadastrado.")
        family = db.get(Family, family_id) if family_id else Family(name=family_name)
        if family is None:
            raise ValueError("Família não encontrada.")
        db.add(family)
        user = User(name=name, email=email, password_hash=passwords.hash(password))
        db.add(user)
        db.flush()
        db.add(Membership(user_id=user.id, family_id=family.id))
        return family.id, user.id


def reset_password(email, password):
    if len(password) < 12:
        raise ValueError("Use uma senha com pelo menos 12 caracteres.")
    with Session(engine) as db, db.begin():
        user = db.scalar(select(User).where(User.email == email.strip().lower()))
        if not user:
            raise ValueError("Usuário não encontrado.")
        user.password_hash = passwords.hash(password)
        db.execute(update(LoginSession).where(LoginSession.user_id == user.id).values(revoked=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["create-user", "reset-password"])
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Integrante")
    parser.add_argument("--family-name", default="Minha família")
    parser.add_argument("--family-id")
    args = parser.parse_args()
    password = getpass("Senha (mínimo 12 caracteres): ")
    if args.action == "create-user":
        family, user = provision(args.family_name, args.name, args.email, password, args.family_id)
        print(f"Usuário criado: {user}; família: {family}")
    else:
        reset_password(args.email, password)
        print("Senha atualizada; sessões revogadas.")


if __name__ == "__main__":
    main()
