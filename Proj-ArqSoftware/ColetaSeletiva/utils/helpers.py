# utils/helpers.py
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity
from models.usuario import Usuario, TipoUsuario


def require_role(*roles):
    """Decorator para exigir tipo de usuário específico"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get("tipo") not in roles:
                return jsonify({"erro": "Acesso negado. Permissão insuficiente."}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_usuario_atual() -> Usuario:
    usuario_id = int(get_jwt_identity())
    return Usuario.query.get_or_404(usuario_id)


def paginar(query, pagina: int, por_pagina: int) -> dict:
    p = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
    return {
        "total": p.total,
        "paginas": p.pages,
        "pagina_atual": p.page,
        "por_pagina": p.per_page,
        "items": p.items,
    }


def sucesso(dados=None, mensagem="OK", status=200):
    resposta = {"sucesso": True, "mensagem": mensagem}
    if dados is not None:
        resposta["dados"] = dados
    return jsonify(resposta), status


def erro(mensagem="Erro interno", status=400, detalhes=None):
    resposta = {"sucesso": False, "erro": mensagem}
    if detalhes:
        resposta["detalhes"] = detalhes
    return jsonify(resposta), status
