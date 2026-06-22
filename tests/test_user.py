from __future__ import annotations

import pytest
from backend.models import User


class TestUser:
    def test_create_user(self, db_session):
        """Deve criar um usuario com valores padrao."""
        user = User(email="teste@teste.com", password_hash="salt$hash")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert len(user.id) == 36
        assert user.email == "teste@teste.com"
        assert user.password_hash == "salt$hash"
        assert user.auth_token is None
        assert user.created_at is not None

    def test_user_email_unique(self, db_session):
        """Emails duplicados devem ser rejeitados."""
        from sqlalchemy.exc import IntegrityError

        u1 = User(email="dup@teste.com", password_hash="h1")
        u2 = User(email="dup@teste.com", password_hash="h2")
        db_session.add(u1)
        db_session.commit()

        db_session.add(u2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_auth_token(self, db_session):
        """Deve armazenar e recuperar auth_token."""
        user = User(email="token@teste.com", password_hash="h", auth_token="abc-123")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.auth_token == "abc-123"

    def test_user_sessions_relationship(self, db_session):
        """Usuario pode ter sessoes vinculadas."""
        from backend.models import Session

        user = User(email="sess@teste.com", password_hash="h")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        s1 = Session(user_id=user.id)
        s2 = Session(user_id=user.id)
        db_session.add_all([s1, s2])
        db_session.commit()

        assert len(user.sessions) == 2

    def test_delete_user_cascades_sessions(self, db_session):
        """Deletar usuario deve remover sessoes vinculadas."""
        from backend.models import Session

        user = User(email="del@teste.com", password_hash="h")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        sess = Session(user_id=user.id)
        db_session.add(sess)
        db_session.commit()

        db_session.delete(user)
        db_session.commit()

        remaining = db_session.query(Session).filter(Session.user_id == user.id).all()
        assert len(remaining) == 0