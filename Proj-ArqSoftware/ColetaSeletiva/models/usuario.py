from datetime import datetime
from extensions import db
import bcrypt


class TipoUsuario:
    CIDADAO = "cidadao"
    PREFEITURA = "prefeitura"
    COOPERATIVA = "cooperativa"


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default=TipoUsuario.CIDADAO)
    cpf_cnpj = db.Column(db.String(20), unique=True, nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    bairro = db.Column(db.String(100), nullable=True)
    cidade = db.Column(db.String(100), nullable=True, default="EcoCidade")
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    pontos_conta = db.relationship("PontosConta", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    coletas = db.relationship("Coleta", back_populates="usuario", lazy="dynamic")
    notificacoes = db.relationship("Notificacao", back_populates="usuario", lazy="dynamic")
    historico_pontos = db.relationship("HistoricoPontos", back_populates="usuario", lazy="dynamic")

    def set_senha(self, senha: str):
        salt = bcrypt.gensalt()
        self.senha_hash = bcrypt.hashpw(senha.encode("utf-8"), salt).decode("utf-8")

    def verificar_senha(self, senha: str) -> bool:
        return bcrypt.checkpw(senha.encode("utf-8"), self.senha_hash.encode("utf-8"))

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "tipo": self.tipo,
            "telefone": self.telefone,
            "bairro": self.bairro,
            "cidade": self.cidade,
            "ativo": self.ativo,
            "criado_em": self.criado_em.isoformat(),
        }

    def __repr__(self):
        return f"<Usuario {self.email} [{self.tipo}]>"


class PontosConta(db.Model):
    __tablename__ = "pontos_conta"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False, unique=True)
    saldo = db.Column(db.Integer, default=0, nullable=False)
    total_acumulado = db.Column(db.Integer, default=0, nullable=False)
    total_resgatado = db.Column(db.Integer, default=0, nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    usuario = db.relationship("Usuario", back_populates="pontos_conta")

    def creditar(self, quantidade: int, descricao: str = ""):
        self.saldo += quantidade
        self.total_acumulado += quantidade

    def debitar(self, quantidade: int) -> bool:
        if self.saldo < quantidade:
            return False
        self.saldo -= quantidade
        self.total_resgatado += quantidade
        return True

    def to_dict(self):
        return {
            "saldo": self.saldo,
            "total_acumulado": self.total_acumulado,
            "total_resgatado": self.total_resgatado,
        }


class HistoricoPontos(db.Model):
    __tablename__ = "historico_pontos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # credito / debito
    descricao = db.Column(db.String(255), nullable=False)
    referencia_id = db.Column(db.Integer, nullable=True)
    referencia_tipo = db.Column(db.String(50), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship("Usuario", back_populates="historico_pontos")

    def to_dict(self):
        return {
            "id": self.id,
            "quantidade": self.quantidade,
            "tipo": self.tipo,
            "descricao": self.descricao,
            "criado_em": self.criado_em.isoformat(),
        }


class Beneficio(db.Model):
    __tablename__ = "beneficios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    custo_pontos = db.Column(db.Integer, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)  # transporte, evento, desconto
    disponivel = db.Column(db.Boolean, default=True)
    quantidade_estoque = db.Column(db.Integer, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    resgates = db.relationship("ResgateBeneficio", back_populates="beneficio", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "custo_pontos": self.custo_pontos,
            "categoria": self.categoria,
            "disponivel": self.disponivel,
            "quantidade_estoque": self.quantidade_estoque,
        }


class ResgateBeneficio(db.Model):
    __tablename__ = "resgates_beneficios"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    beneficio_id = db.Column(db.Integer, db.ForeignKey("beneficios.id"), nullable=False)
    pontos_utilizados = db.Column(db.Integer, nullable=False)
    codigo_resgate = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default="ativo")  # ativo, utilizado, expirado
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    utilizado_em = db.Column(db.DateTime, nullable=True)

    usuario = db.relationship("Usuario")
    beneficio = db.relationship("Beneficio", back_populates="resgates")

    def to_dict(self):
        return {
            "id": self.id,
            "beneficio": self.beneficio.to_dict() if self.beneficio else None,
            "pontos_utilizados": self.pontos_utilizados,
            "codigo_resgate": self.codigo_resgate,
            "status": self.status,
            "criado_em": self.criado_em.isoformat(),
        }