from __future__ import annotations

from datetime import datetime, timezone

import pytest
from backend.models import ChatMessage, Session


def _make_session(db_session, title: str | None = None) -> Session:
    """Helper para criar Session nos testes."""
    sess = Session(title=title)
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)
    return sess


class TestSession:
    def test_create_session_defaults(self, db_session):
        """Deve criar uma sessao com valores padrao (id UUID, title None, timestamps)."""
        sess = Session()
        db_session.add(sess)
        db_session.commit()
        db_session.refresh(sess)

        assert sess.id is not None
        assert len(sess.id) == 36  # UUID length
        assert sess.title is None
        assert isinstance(sess.created_at, datetime)
        assert isinstance(sess.updated_at, datetime)
        # created_at e updated_at podem diferir por microssegundos
        # pois cada coluna chama _utcnow() independentemente
        diff = abs((sess.updated_at - sess.created_at).total_seconds())
        assert diff < 1.0

    def test_create_session_with_title(self, db_session):
        """Deve criar uma sessao com titulo definido."""
        sess = Session(title="Minha Sessao")
        db_session.add(sess)
        db_session.commit()
        db_session.refresh(sess)

        assert sess.title == "Minha Sessao"

    def test_session_auto_updates_updated_at(self, db_session):
        """Ao atualizar a sessao, updated_at deve ser alterado."""
        sess = Session()
        db_session.add(sess)
        db_session.commit()

        original_updated = sess.updated_at

        sess.title = "Novo Titulo"
        db_session.commit()
        db_session.refresh(sess)

        assert sess.title == "Novo Titulo"
        assert sess.updated_at > original_updated

    def test_session_uuid_unique(self, db_session):
        """Sessoes diferentes devem ter UUIDs diferentes."""
        s1 = Session()
        s2 = Session()
        db_session.add_all([s1, s2])
        db_session.commit()

        assert s1.id != s2.id

    def test_session_relationship_messages(self, db_session):
        """Session.messages deve retornar as ChatMessage vinculadas."""
        sess = Session()
        db_session.add(sess)
        db_session.commit()
        db_session.refresh(sess)

        msg1 = ChatMessage(session_key=sess.id, role="user", content="msg1")
        msg2 = ChatMessage(session_key=sess.id, role="assistant", content="msg2")
        db_session.add_all([msg1, msg2])
        db_session.commit()

        assert len(sess.messages) == 2
        assert sess.messages[0].content == "msg1"
        assert sess.messages[1].content == "msg2"

    def test_delete_session_cascades_messages(self, db_session):
        """Ao deletar uma sessao, as mensagens vinculadas devem ser removidas."""
        sess = Session()
        db_session.add(sess)
        db_session.commit()
        db_session.refresh(sess)

        msg = ChatMessage(session_key=sess.id, role="user", content="sera removida")
        db_session.add(msg)
        db_session.commit()

        db_session.delete(sess)
        db_session.commit()

        remaining = db_session.query(ChatMessage).filter(ChatMessage.session_key == sess.id).all()
        assert len(remaining) == 0

    def test_query_sessions_ordered_by_updated_at(self, db_session):
        """Sessoes devem ser ordenaveis por updated_at DESC."""
        import time as time_module

        s1 = Session(title="primeira")
        db_session.add(s1)
        db_session.commit()
        time_module.sleep(0.01)

        s2 = Session(title="segunda")
        db_session.add(s2)
        db_session.commit()

        results = db_session.query(Session).order_by(Session.updated_at.desc()).all()
        assert results[0].title == "segunda"
        assert results[1].title == "primeira"


class TestChatMessage:
    def _create_session(self, db_session) -> Session:
        return _make_session(db_session)

    def test_create_message_defaults(self, db_session):
        """Deve criar uma mensagem com valores padrao para model e created_at."""
        sess = self._create_session(db_session)
        msg = ChatMessage(
            session_key=sess.id,
            role="user",
            content="Ola, mundo!",
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.id is not None
        assert msg.session_key == sess.id
        assert msg.role == "user"
        assert msg.content == "Ola, mundo!"
        assert msg.model == "google/gemma-4-31b-it"
        assert isinstance(msg.created_at, datetime)

    def test_create_message_custom_model(self, db_session):
        """Deve criar uma mensagem com modelo customizado."""
        sess = self._create_session(db_session)
        msg = ChatMessage(
            session_key=sess.id,
            role="user",
            content="Teste",
            model="openai/gpt-4o",
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.model == "openai/gpt-4o"

    def test_query_by_session_key(self, db_session):
        """Deve filtrar mensagens por session_key."""
        sess1 = _make_session(db_session)
        sess2 = _make_session(db_session)
        msg1 = ChatMessage(session_key=sess1.id, role="user", content="a")
        msg2 = ChatMessage(session_key=sess2.id, role="user", content="b")
        db_session.add_all([msg1, msg2])
        db_session.commit()

        results = (
            db_session.query(ChatMessage)
            .filter(ChatMessage.session_key == sess1.id)
            .all()
        )
        assert len(results) == 1
        assert results[0].content == "a"

    def test_query_by_role(self, db_session):
        """Deve filtrar mensagens pelo campo role."""
        sess = self._create_session(db_session)
        msg1 = ChatMessage(session_key=sess.id, role="user", content="pergunta")
        msg2 = ChatMessage(session_key=sess.id, role="assistant", content="resposta")
        db_session.add_all([msg1, msg2])
        db_session.commit()

        users = (
            db_session.query(ChatMessage)
            .filter(ChatMessage.role == "user")
            .all()
        )
        assistants = (
            db_session.query(ChatMessage)
            .filter(ChatMessage.role == "assistant")
            .all()
        )

        assert len(users) == 1
        assert len(assistants) == 1
        assert users[0].content == "pergunta"
        assert assistants[0].content == "resposta"

    def test_created_at_auto_set(self, db_session):
        """O campo created_at deve ser preenchido automaticamente com UTC now."""
        sess = self._create_session(db_session)
        before = datetime.now(timezone.utc).replace(tzinfo=None)
        msg = ChatMessage(session_key=sess.id, role="user", content="timestamp test")
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)
        after = datetime.now(timezone.utc).replace(tzinfo=None)

        assert before <= msg.created_at <= after

    def test_foreign_key_session(self, db_session):
        """Nao deve permitir criar mensagem com session_key invalida."""
        from sqlalchemy.exc import IntegrityError

        msg = ChatMessage(
            session_key="uuid-inexistente",
            role="user",
            content="teste",
        )
        db_session.add(msg)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_content_persists_long_text(self, db_session):
        """Deve persistir conteudos longos corretamente."""
        sess = self._create_session(db_session)
        long_text = "Lorem ipsum " * 200
        msg = ChatMessage(session_key=sess.id, role="user", content=long_text)
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.content == long_text
