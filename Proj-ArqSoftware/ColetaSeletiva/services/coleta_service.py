from datetime import datetime
from flask import current_app
from extensions import db
from models.coleta import Coleta, MaterialColeta, StatusColeta
from models.ponto_coleta import Notificacao
from models.usuario import TipoUsuario, Usuario
from services.usuario_service import usuario_service


class ColetaService:

    def agendar(self, usuario_id: int, dados: dict) -> tuple[dict, int]:
        coleta = Coleta(
            usuario_id=usuario_id,
            endereco=dados["endereco"],
            complemento=dados.get("complemento"),
            bairro=dados["bairro"],
            cidade=dados.get("cidade", "EcoCidade"),
            latitude=dados.get("latitude"),
            longitude=dados.get("longitude"),
            data_agendada=datetime.fromisoformat(dados["data_agendada"]),
            observacoes=dados.get("observacoes"),
        )
        db.session.add(coleta)
        db.session.flush()

        for mat in dados.get("materiais", []):
            material = MaterialColeta(
                coleta_id=coleta.id,
                tipo=mat["tipo"],
                quantidade_kg=mat.get("quantidade_kg"),
                observacao=mat.get("observacao"),
            )
            db.session.add(material)

        # Notifica prefeitura/cooperativas
        self._notificar_gestores(coleta)
        db.session.commit()

        return {"mensagem": "Coleta agendada com sucesso!", "coleta": coleta.to_dict(detalhado=True)}, 201

    def listar_por_usuario(self, usuario_id: int, status: str = None) -> list:
        query = Coleta.query.filter_by(usuario_id=usuario_id)
        if status:
            query = query.filter_by(status=status)
        coletas = query.order_by(Coleta.data_agendada.desc()).all()
        return [c.to_dict() for c in coletas]

    def listar_todas(self, status: str = None, bairro: str = None,
                     cooperativa_id: int = None, pagina: int = 1, por_pagina: int = 20) -> dict:
        query = Coleta.query
        if status:
            query = query.filter_by(status=status)
        if bairro:
            query = query.filter(Coleta.bairro.ilike(f"%{bairro}%"))
        if cooperativa_id:
            query = query.filter_by(cooperativa_id=cooperativa_id)

        paginacao = query.order_by(Coleta.criado_em.desc()).paginate(page=pagina, per_page=por_pagina, error_out=False)
        return {
            "coletas": [c.to_dict() for c in paginacao.items],
            "total": paginacao.total,
            "paginas": paginacao.pages,
            "pagina_atual": pagina,
        }

    def obter(self, coleta_id: int) -> dict:
        coleta = Coleta.query.get_or_404(coleta_id)
        return coleta.to_dict(detalhado=True)

    def atualizar_status(self, coleta_id: int, novo_status: str,
                         cooperativa_id: int = None, dados_extras: dict = None) -> tuple[dict, int]:
        coleta = Coleta.query.get_or_404(coleta_id)
        status_validos = [StatusColeta.ACEITA, StatusColeta.EM_ROTA,
                          StatusColeta.REALIZADA, StatusColeta.CANCELADA]
        if novo_status not in status_validos:
            return {"erro": "Status inválido"}, 400

        coleta.status = novo_status

        if cooperativa_id and not coleta.cooperativa_id:
            coleta.cooperativa_id = cooperativa_id

        if novo_status == StatusColeta.REALIZADA:
            coleta.data_realizada = datetime.utcnow()
            if dados_extras:
                for mat in coleta.materiais:
                    info = dados_extras.get("materiais", {}).get(str(mat.id))
                    if info:
                        mat.quantidade_kg = info.get("quantidade_kg", mat.quantidade_kg)
            self._conceder_pontos_coleta(coleta)

        # Notifica o cidadão
        self._notificar_cidadao(coleta, novo_status)
        db.session.commit()

        return {"mensagem": f"Status atualizado para {novo_status}", "coleta": coleta.to_dict(detalhado=True)}, 200

    def cancelar(self, coleta_id: int, usuario_id: int) -> tuple[dict, int]:
        coleta = Coleta.query.get_or_404(coleta_id)
        if coleta.usuario_id != usuario_id:
            return {"erro": "Sem permissão"}, 403
        if coleta.status in [StatusColeta.REALIZADA, StatusColeta.CANCELADA]:
            return {"erro": f"Não é possível cancelar coleta com status '{coleta.status}'"}, 400
        coleta.status = StatusColeta.CANCELADA
        db.session.commit()
        return {"mensagem": "Coleta cancelada"}, 200

    def _conceder_pontos_coleta(self, coleta: Coleta):
        pontos = current_app.config.get("PONTOS_POR_COLETA", 50)
        usuario_service.creditar_pontos(
            usuario_id=coleta.usuario_id,
            quantidade=pontos,
            descricao=f"Coleta domiciliar realizada (#{coleta.id})",
            referencia_id=coleta.id,
            referencia_tipo="coleta",
        )

    def _notificar_gestores(self, coleta: Coleta):
        gestores = Usuario.query.filter(
            Usuario.tipo.in_([TipoUsuario.PREFEITURA, TipoUsuario.COOPERATIVA]),
            Usuario.ativo == True
        ).all()
        for gestor in gestores:
            notif = Notificacao(
                usuario_id=gestor.id,
                titulo="Nova solicitação de coleta",
                mensagem=f"Coleta agendada em {coleta.bairro} para {coleta.data_agendada.strftime('%d/%m/%Y %H:%M')}",
                tipo="coleta",
                referencia_id=coleta.id,
            )
            db.session.add(notif)

    def _notificar_cidadao(self, coleta: Coleta, status: str):
        msgs = {
            StatusColeta.ACEITA: ("Coleta aceita! ✅", "Sua coleta foi aceita e está agendada."),
            StatusColeta.EM_ROTA: ("Caminhão a caminho! 🚛", "O veículo de coleta está se dirigindo até você."),
            StatusColeta.REALIZADA: ("Coleta concluída! 🎉", f"Parabéns! Você ganhou {current_app.config.get('PONTOS_POR_COLETA', 50)} pontos."),
            StatusColeta.CANCELADA: ("Coleta cancelada ❌", "Sua coleta foi cancelada."),
        }
        if status in msgs:
            titulo, mensagem = msgs[status]
            notif = Notificacao(
                usuario_id=coleta.usuario_id,
                titulo=titulo,
                mensagem=mensagem,
                tipo="coleta",
                referencia_id=coleta.id,
            )
            db.session.add(notif)


coleta_service = ColetaService()
