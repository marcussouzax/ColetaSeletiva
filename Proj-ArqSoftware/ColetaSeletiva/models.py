from app import db
from datetime import datetime


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    data_cadastro = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    coletas = db.relationship(
        'Coleta',
        backref='usuario',
        lazy=True
    )

    def __repr__(self):
        return f'<Usuario {self.nome}>'


class Material(db.Model):
    __tablename__ = 'materiais'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)

    coletas = db.relationship(
        'Coleta',
        backref='material',
        lazy=True
    )

    def __repr__(self):
        return f'<Material {self.nome}>'


class Coleta(db.Model):
    __tablename__ = 'coletas'

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id'),
        nullable=False
    )

    material_id = db.Column(
        db.Integer,
        db.ForeignKey('materiais.id'),
        nullable=False
    )

    quantidade = db.Column(db.Float)

    endereco = db.Column(
        db.String(255),
        nullable=False
    )

    data_coleta = db.Column(
        db.Date,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default='Pendente'
    )

    def __repr__(self):
        return f'<Coleta {self.id}>'