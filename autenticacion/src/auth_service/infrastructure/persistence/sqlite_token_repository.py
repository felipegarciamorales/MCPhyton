from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from auth_service.domain.entities.token import Token, TokenType
from auth_service.domain.repositories.token_repository import TokenRepository
from auth_service.infrastructure.persistence.models import TokenModel
from auth_service.shared.clock import ensure_utc


class SqliteTokenRepository(TokenRepository):
    """SQLAlchemy-backed implementation of the TokenRepository port."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, token: Token) -> Token:
        model = TokenModel(
            jti=token.jti,
            user_id=token.user_id,
            token_type=token.token_type.value,
            expires_at=token.expires_at,
            revoked=token.revoked,
            created_at=token.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def get_by_jti(self, jti: str) -> Optional[Token]:
        statement = select(TokenModel).where(TokenModel.jti == jti)
        model = self._session.scalars(statement).first()
        return self._to_entity(model) if model else None

    def revoke(self, jti: str) -> None:
        self._session.execute(update(TokenModel).where(TokenModel.jti == jti).values(revoked=True))
        self._session.commit()

    def revoke_all_for_user(self, user_id: int, token_type: Optional[str] = None) -> None:
        statement = update(TokenModel).where(TokenModel.user_id == user_id).values(revoked=True)
        if token_type is not None:
            statement = statement.where(TokenModel.token_type == token_type)
        self._session.execute(statement)
        self._session.commit()

    @staticmethod
    def _to_entity(model: TokenModel) -> Token:
        return Token(
            id=model.id,
            jti=model.jti,
            user_id=model.user_id,
            token_type=TokenType(model.token_type),
            expires_at=ensure_utc(model.expires_at),
            revoked=model.revoked,
            created_at=ensure_utc(model.created_at),
        )
