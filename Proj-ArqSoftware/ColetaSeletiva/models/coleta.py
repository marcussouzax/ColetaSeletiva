from datetime import datetime
from extensions import db


class StatusColeta:
    PENDENTE = "pendente"
    ACEITA = "aceita"
    EM_ROTA = "em_rota"
    REALIZADA = "realizada"
    CANCELADA = "cancelada"


class TipoMaterial:
    PLASTICO = "plastico"
    PAPEL = "papel"
    VIDRO = "vidro"
    METAL = "metal"
    ELETRONICO = "eletronico"
    ORGANICO = "organico"
    MISTO = "misto"


class Coleta(db.Model):
    __tablename__ = "coletas"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    cooperativa_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    endereco = db.Column(db.String(255), nullable=False)
    complemento = db.Column(db.String(100), nullable=True)
    bairro = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(100), nullable=False, default="EcoCidade")
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    data_agendada = db.Column(db.DateTime, nullable=False)
    data_realizada = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default=StatusColeta.PENDENTE, index=True)
    observacoes = db.Column(db.Text, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    usuario = db.relationship("Usuario", foreign_keys=[usuario_id], back_populates="coletas")
    cooperativa = db.relationship("Usuario", foreign_keys=[cooperativa_id])
    materiais = db.relationship("MaterialColeta", back_populates="coleta", cascade="all, delete-orphan")

    @property
    def total_kg(self):
        return sum(m.quantidade_kg for m in self.materiais if m.quantidade_kg)

    def to_dict(self, detalhado=False):
        data = {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "endereco": self.endereco,
            "complemento": self.complemento,
            "bairro": self.bairro,
            "cidade": self.cidade,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "data_agendada": self.data_agendada.isoformat(),
            "data_realizada": self.data_realizada.isoformat() if self.data_realizada else None,
            "status": self.status,
            "observacoes": self.observacoes,
            "total_kg": self.total_kg,
            "criado_em": self.criado_em.isoformat(),
        }
        if detalhado:
            data["materiais"] = [m.to_dict() for m in self.materiais]
            data["cooperativa"] = self.cooperativa.nome if self.cooperativa else None
        return data

    def __repr__(self):
        return f"<Coleta {self.id} [{self.status}]>"


class MaterialColeta(db.Model):
    __tablename__ = "materiais_coleta"

    id = db.Column(db.Integer, primary_key=True)
    coleta_id = db.Column(db.Integer, db.ForeignKey("coletas.id"), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)
    quantidade_kg = db.Column(db.Float, nullable=True)
    observacao = db.Column(db.String(255), nullable=True)

    coleta = db.relationship("Coleta", back_populates="materiais")

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "quantidade_kg": self.quantidade_kg,
            "observacao": self.observacao,
        }