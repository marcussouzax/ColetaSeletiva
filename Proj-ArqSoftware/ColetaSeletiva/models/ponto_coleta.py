from datetime import datetime
from extensions import db


class Ecoponto(db.Model):
    __tablename__ = "ecopontos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    endereco = db.Column(db.String(255), nullable=False)
    bairro = db.Column(db.String(100), nullable=False, index=True)
    cidade = db.Column(db.String(100), nullable=False, default="EcoCidade")
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    horario_funcionamento = db.Column(db.String(200), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    responsavel = db.Column(db.String(120), nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    materiais_aceitos = db.relationship("MaterialEcoponto", back_populates="ecoponto", cascade="all, delete-orphan")

    def to_dict(self, incluir_materiais=True):
        data = {
            "id": self.id,
            "nome": self.nome,
            "endereco": self.endereco,
            "bairro": self.bairro,
            "cidade": self.cidade,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "horario_funcionamento": self.horario_funcionamento,
            "telefone": self.telefone,
            "responsavel": self.responsavel,
            "ativo": self.ativo,
        }
        if incluir_materiais:
            data["materiais_aceitos"] = [m.to_dict() for m in self.materiais_aceitos]
        return data

    def __repr__(self):
        return f"<Ecoponto {self.nome}>"


class MaterialEcoponto(db.Model):
    __tablename__ = "materiais_ecoponto"

    id = db.Column(db.Integer, primary_key=True)
    ecoponto_id = db.Column(db.Integer, db.ForeignKey("ecopontos.id"), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)

    ecoponto = db.relationship("Ecoponto", back_populates="materiais_aceitos")

    def to_dict(self):
        return {"tipo": self.tipo, "descricao": self.descricao}


class NotificacaoBairro(db.Model):
    """Agendamentos de coleta por bairro (calendário municipal)"""
    __tablename__ = "notificacoes_bairro"

    id = db.Column(db.Integer, primary_key=True)
    bairro = db.Column(db.String(100), nullable=False, index=True)
    data_coleta = db.Column(db.DateTime, nullable=False)
    turno = db.Column(db.String(20), nullable=True)  # manha, tarde, noite
    descricao = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "bairro": self.bairro,
            "data_coleta": self.data_coleta.isoformat(),
            "turno": self.turno,
            "descricao": self.descricao,
        }


class Notificacao(db.Model):
    """Notificações individuais para cidadãos"""
    __tablename__ = "notificacoes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    titulo = db.Column(db.String(120), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(30), nullable=False)  # coleta, pontos, sistema, bairro
    lida = db.Column(db.Boolean, default=False)
    referencia_id = db.Column(db.Integer, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship("Usuario", back_populates="notificacoes")

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "mensagem": self.mensagem,
            "tipo": self.tipo,
            "lida": self.lida,
            "criado_em": self.criado_em.isoformat(),
        }