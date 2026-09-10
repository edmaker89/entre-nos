import hashlib
import json
import logging
from contextlib import contextmanager
from uuid import uuid4

from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Family, Idempotency
from app.main import AppError

engine = create_engine(settings.database_url, pool_size=3, max_overflow=2, pool_pre_ping=True)
logger = logging.getLogger('expense')


def family_context(session, family_id, lock=True):
    session.execute(text('SET LOCAL ROLE expense_app'))
    session.execute(text("SELECT set_config('app.family_id', :family, true)"), {'family':family_id})
    stmt=select(Family).where(Family.id==family_id)
    if lock:
        stmt=stmt.with_for_update()
    if session.scalar(stmt) is None:
        raise AppError('not_found','Família não encontrada.',404)


@contextmanager
def transaction(family_id, bind=None):
    try:
        with Session(bind or engine) as session, session.begin():
            family_context(session,family_id)
            yield session
    except SQLAlchemyError:
        operation_id=str(uuid4())
        logger.error('database_error operation_id=%s',operation_id)
        raise AppError('database_unavailable','Não foi possível confirmar a gravação. Tente novamente.',503) from None


def mutate(session, family_id, key, payload, action):
    if not key or len(key)>200:
        raise AppError('idempotency_required','Informe a chave da operação.',422)
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()
    previous=session.scalar(select(Idempotency).where(Idempotency.family_id==family_id,Idempotency.key==key))
    if previous:
        if previous.payload_hash!=digest:
            raise AppError('idempotency_conflict','Chave já utilizada com conteúdo diferente.')
        return previous.result
    result=action()
    session.add(Idempotency(family_id=family_id,key=key,payload_hash=digest,result=result))
    session.flush()
    return result


def check_version(row, expected):
    if row is None or getattr(row,'deleted_at',None):
        raise AppError('not_found','Registro não encontrado.',404)
    if row.version!=expected:
        raise AppError('version_conflict','Registro alterado em outra sessão. Recarregue.')
    row.version+=1
