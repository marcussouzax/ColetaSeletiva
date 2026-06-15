from datetime import datetime
from extensions import db


class StatusRota:
    PLANEJADA = "planejada"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class Rota(db.Model):
    __tablename__ = "rotas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cooperativa_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    data_planejada = db.Column(db.DateTime, nullable=False)
    data_inicio = db.Column(db.DateTime, nullable=True)
    data_fim = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default=StatusRota.PLANEJADA, nullable=False)
    distancia_total_km = db.Column(db.Float, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    cooperativa = db.relationship("Usuario", foreign_keys=[cooperativa_id])
    paradas = db.relationship("ParadaRota", back_populates="rota", order_by="ParadaRota.ordem", cascade="all, delete-orphan")

    def to_dict(self, detalhado=False):
        data = {
            "id": self.id,
            "nome": self.nome,
            "cooperativa_id": self.cooperativa_id,
            "data_planejada": self.data_planejada.isoformat(),
            "data_inicio": self.data_inicio.isoformat() if self.data_inicio else None,
            "data_fim": self.data_fim.isoformat() if self.data_fim else None,
            "status": self.status,
            "distancia_total_km": self.distancia_total_km,
            "total_paradas": len(self.paradas),
        }
        if detalhado:
            data["paradas"] = [p.to_dict() for p in self.paradas]
        return data


class ParadaRota(db.Model):
    __tablename__ = "paradas_rota"

    id = db.Column(db.Integer, primary_key=True)
    rota_id = db.Column(db.Integer, db.ForeignKey("rotas.id"), nullable=False)
    coleta_id = db.Column(db.Integer, db.ForeignKey("coletas.id"), nullable=True)
    ecoponto_id = db.Column(db.Integer, db.ForeignKey("ecopontos.id"), nullable=True)
    ordem = db.Column(db.Integer, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    endereco = db.Column(db.String(255), nullable=False)
    concluida = db.Column(db.Boolean, default=False)
    concluida_em = db.Column(db.DateTime, nullable=True)

    rota = db.relationship("Rota", back_populates="paradas")

    def to_dict(self):
        return {
            "id": self.id,
            "ordem": self.ordem,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "endereco": self.endereco,
            "coleta_id": self.coleta_id,
            "ecoponto_id": self.ecoponto_id,
            "concluida": self.concluida,
        }
