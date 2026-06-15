from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# MODELO
class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)

# Dados fixos
pontos = [
    {"nome": "Eco Centro Recife", "endereco": "Boa Vista"},
    {"nome": "Ponto Sul Reciclagem", "endereco": "Zona Sul"},
    {"nome": "Coleta Olinda", "endereco": "Olinda - PE"}
]

coletas = 0

# Cria as tabelas
with app.app_context():
    db.create_all()
    print("BANCO ATIVO:", app.config["SQLALCHEMY_DATABASE_URI"])

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/usuarios/registrar", methods=["POST"])
def registrar_usuario():
    data = request.json

    if Usuario.query.filter_by(email=data["email"]).first():
        return jsonify({"erro": "Email já cadastrado"}), 400

    usuario = Usuario(
        nome=data["nome"],
        email=data["email"],
        senha=generate_password_hash(data["senha"])
    )

    db.session.add(usuario)
    db.session.commit()

    return jsonify({"message": "Usuário cadastrado com sucesso!"})

@app.route("/api/pontos")
def get_pontos():
    return jsonify(pontos)

@app.route("/api/stats")
def stats():
    total_usuarios = Usuario.query.count()

    return jsonify({
        "usuarios": total_usuarios,
        "pontos": len(pontos),
        "coletas": coletas
    })

@app.route("/api/relatorios")
def relatorio():

    usuarios = Usuario.query.all()

    usuarios_safe = [
        {
            "nome": u.nome,
            "email": u.email
        }
        for u in usuarios
    ]

    return jsonify({
        "titulo": "Relatório EcoCidade",
        "total_usuarios": len(usuarios_safe),
        "total_pontos": len(pontos),
        "total_coletas": coletas,
        "usuarios": usuarios_safe
    })

if __name__ == "__main__":
    app.run(debug=True)