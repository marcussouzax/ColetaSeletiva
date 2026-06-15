from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.usuario_service import usuario_service
from utils.helpers import require_role, erro
from utils.validators import validar_email, validar_campos_obrigatorios
from models.usuario import TipoUsuario

usuario_bp = Blueprint("usuario", __name__, url_prefix="/api/usuarios")


@usuario_bp.post("/registrar")
def registrar():
    dados = request.get_json() or {}
    faltando = validar_campos_obrigatorios(dados, ["nome", "email", "senha"])
    if faltando:
        return erro(f"Campos obrigatórios faltando: {', '.join(faltando)}")
    if not validar_email(dados["email"]):
        return erro("E-mail inválido")
    resultado, status = usuario_service.registrar(dados)
    return jsonify(resultado), status


@usuario_bp.post("/login")
def login():
    dados = request.get_json() or {}
    faltando = validar_campos_obrigatorios(dados, ["email", "senha"])
    if faltando:
        return erro(f"Campos obrigatórios faltando: {', '.join(faltando)}")
    resultado, status = usuario_service.login(dados["email"], dados["senha"])
    return jsonify(resultado), status


@usuario_bp.get("/perfil")
@jwt_required()
def perfil():
    usuario_id = int(get_jwt_identity())
    return jsonify(usuario_service.obter_perfil(usuario_id)), 200


@usuario_bp.put("/perfil")
@jwt_required()
def atualizar_perfil():
    usuario_id = int(get_jwt_identity())
    dados = request.get_json() or {}
    resultado, status = usuario_service.atualizar_perfil(usuario_id, dados)
    return jsonify(resultado), status


@usuario_bp.get("/pontos")
@jwt_required()
def meus_pontos():
    usuario_id = int(get_jwt_identity())
    resultado, status = usuario_service.obter_pontos(usuario_id)
    return jsonify(resultado), status


@usuario_bp.get("/beneficios")
@jwt_required()
def listar_beneficios():
    return jsonify(usuario_service.listar_beneficios()), 200


@usuario_bp.post("/beneficios/<int:beneficio_id>/resgatar")
@jwt_required()
def resgatar_beneficio(beneficio_id):
    usuario_id = int(get_jwt_identity())
    resultado, status = usuario_service.resgatar_beneficio(usuario_id, beneficio_id)
    return jsonify(resultado), status


# --- Rotas admin (prefeitura) ---
@usuario_bp.get("/")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA)
def listar_usuarios():
    from models.usuario import Usuario
    tipo = request.args.get("tipo")
    query = Usuario.query
    if tipo:
        query = query.filter_by(tipo=tipo)
    usuarios = query.all()
    return jsonify([u.to_dict() for u in usuarios]), 200


@usuario_bp.delete("/<int:usuario_id>")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA)
def desativar_usuario(usuario_id):
    from models.usuario import Usuario
    from extensions import db
    u = Usuario.query.get_or_404(usuario_id)
    u.ativo = False
    db.session.commit()
    return jsonify({"mensagem": "Usuário desativado"}), 200
