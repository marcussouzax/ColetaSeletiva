from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from extensions import db
from models.usuario import Usuario, PontosConta, HistoricoPontos, Beneficio, ResgateBeneficio, TipoUsuario
import secrets
import string
from datetime import datetime


class UsuarioService:

    def registrar(self, dados: dict) -> tuple[dict, int]:
        if Usuario.query.filter_by(email=dados["email"]).first():
            return {"erro": "E-mail já cadastrado"}, 409

        usuario = Usuario(
            nome=dados["nome"],
            email=dados["email"],
            tipo=dados.get("tipo", TipoUsuario.CIDADAO),
            cpf_cnpj=dados.get("cpf_cnpj"),
            telefone=dados.get("telefone"),
            bairro=dados.get("bairro"),
            cidade=dados.get("cidade", "EcoCidade"),
        )
        usuario.set_senha(dados["senha"])

        db.session.add(usuario)
        db.session.flush()

        # Cria conta de pontos automática para cidadãos
        if usuario.tipo == TipoUsuario.CIDADAO:
            conta = PontosConta(usuario_id=usuario.id)
            db.session.add(conta)

        db.session.commit()
        return {"mensagem": "Usuário cadastrado com sucesso", "usuario": usuario.to_dict()}, 201

    def login(self, email: str, senha: str) -> tuple[dict, int]:
        usuario = Usuario.query.filter_by(email=email, ativo=True).first()
        if not usuario or not usuario.verificar_senha(senha):
            return {"erro": "Credenciais inválidas"}, 401

        access_token = create_access_token(
            identity=str(usuario.id),
            additional_claims={"tipo": usuario.tipo}
        )
        refresh_token = create_refresh_token(identity=str(usuario.id))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "usuario": usuario.to_dict(),
        }, 200

    def obter_perfil(self, usuario_id: int) -> dict:
        usuario = Usuario.query.get_or_404(usuario_id)
        perfil = usuario.to_dict()
        if usuario.pontos_conta:
            perfil["pontos"] = usuario.pontos_conta.to_dict()
        return perfil

    def atualizar_perfil(self, usuario_id: int, dados: dict) -> tuple[dict, int]:
        usuario = Usuario.query.get_or_404(usuario_id)
        campos_permitidos = ["nome", "telefone", "bairro", "cidade"]
        for campo in campos_permitidos:
            if campo in dados:
                setattr(usuario, campo, dados[campo])
        if "senha" in dados:
            usuario.set_senha(dados["senha"])
        db.session.commit()
        return {"mensagem": "Perfil atualizado", "usuario": usuario.to_dict()}, 200

    def obter_pontos(self, usuario_id: int) -> tuple[dict, int]:
        usuario = Usuario.query.get_or_404(usuario_id)
        if not usuario.pontos_conta:
            return {"erro": "Conta de pontos não encontrada"}, 404
        historico = usuario.historico_pontos.order_by(HistoricoPontos.criado_em.desc()).limit(20).all()
        return {
            "pontos": usuario.pontos_conta.to_dict(),
            "historico": [h.to_dict() for h in historico],
        }, 200

    def creditar_pontos(self, usuario_id: int, quantidade: int, descricao: str,
                        referencia_id: int = None, referencia_tipo: str = None):
        conta = PontosConta.query.filter_by(usuario_id=usuario_id).first()
        if not conta:
            return
        conta.creditar(quantidade, descricao)
        historico = HistoricoPontos(
            usuario_id=usuario_id,
            quantidade=quantidade,
            tipo="credito",
            descricao=descricao,
            referencia_id=referencia_id,
            referencia_tipo=referencia_tipo,
        )
        db.session.add(historico)
        db.session.commit()

    def resgatar_beneficio(self, usuario_id: int, beneficio_id: int) -> tuple[dict, int]:
        beneficio = Beneficio.query.get_or_404(beneficio_id)
        if not beneficio.disponivel:
            return {"erro": "Benefício indisponível"}, 400

        conta = PontosConta.query.filter_by(usuario_id=usuario_id).first()
        if not conta:
            return {"erro": "Conta de pontos não encontrada"}, 404

        if conta.saldo < beneficio.custo_pontos:
            return {"erro": f"Pontos insuficientes. Necessário: {beneficio.custo_pontos}, disponível: {conta.saldo}"}, 400

        if beneficio.quantidade_estoque is not None:
            if beneficio.quantidade_estoque <= 0:
                return {"erro": "Estoque esgotado"}, 400
            beneficio.quantidade_estoque -= 1
            if beneficio.quantidade_estoque == 0:
                beneficio.disponivel = False

        conta.debitar(beneficio.custo_pontos)

        codigo = "ECO-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        resgate = ResgateBeneficio(
            usuario_id=usuario_id,
            beneficio_id=beneficio_id,
            pontos_utilizados=beneficio.custo_pontos,
            codigo_resgate=codigo,
        )
        db.session.add(resgate)

        historico = HistoricoPontos(
            usuario_id=usuario_id,
            quantidade=beneficio.custo_pontos,
            tipo="debito",
            descricao=f"Resgate: {beneficio.nome}",
            referencia_id=beneficio_id,
            referencia_tipo="beneficio",
        )
        db.session.add(historico)
        db.session.commit()

        return {"mensagem": "Benefício resgatado!", "resgate": resgate.to_dict()}, 200

    def listar_beneficios(self) -> list:
        return [b.to_dict() for b in Beneficio.query.filter_by(disponivel=True).all()]


usuario_service = UsuarioService()
