from extensions import db
from models.ponto_coleta import Ecoponto, MaterialEcoponto, NotificacaoBairro, Notificacao
from models.usuario import Usuario, TipoUsuario
from services.mapa_service import mapa_service
from datetime import datetime


class EcopontoService:

    def criar(self, dados: dict) -> tuple[dict, int]:
        # Geocodifica se não tiver coordenadas
        if not dados.get("latitude") or not dados.get("longitude"):
            geo = mapa_service.geocodificar_endereco(dados["endereco"])
            if "erro" not in geo:
                dados["latitude"] = geo["latitude"]
                dados["longitude"] = geo["longitude"]

        ep = Ecoponto(
            nome=dados["nome"],
            endereco=dados["endereco"],
            bairro=dados["bairro"],
            cidade=dados.get("cidade", "EcoCidade"),
            latitude=dados.get("latitude", 0.0),
            longitude=dados.get("longitude", 0.0),
            horario_funcionamento=dados.get("horario_funcionamento"),
            telefone=dados.get("telefone"),
            responsavel=dados.get("responsavel"),
        )
        db.session.add(ep)
        db.session.flush()

        for mat in dados.get("materiais_aceitos", []):
            m = MaterialEcoponto(ecoponto_id=ep.id, tipo=mat["tipo"], descricao=mat.get("descricao"))
            db.session.add(m)

        db.session.commit()
        return {"mensagem": "Ecoponto criado", "ecoponto": ep.to_dict()}, 201

    def listar(self, bairro: str = None, material: str = None, ativo: bool = True) -> list:
        query = Ecoponto.query.filter_by(ativo=ativo)
        if bairro:
            query = query.filter(Ecoponto.bairro.ilike(f"%{bairro}%"))
        ecopontos = query.all()
        if material:
            ecopontos = [
                ep for ep in ecopontos
                if any(m.tipo.lower() == material.lower() for m in ep.materiais_aceitos)
            ]
        return [ep.to_dict() for ep in ecopontos]

    def buscar_proximos(self, latitude: float, longitude: float, raio_km: float = None) -> list:
        return mapa_service.buscar_ecopontos_proximos(latitude, longitude, raio_km)

    def obter(self, ecoponto_id: int) -> dict:
        ep = Ecoponto.query.get_or_404(ecoponto_id)
        return ep.to_dict()

    def atualizar(self, ecoponto_id: int, dados: dict) -> tuple[dict, int]:
        ep = Ecoponto.query.get_or_404(ecoponto_id)
        campos = ["nome", "endereco", "bairro", "cidade", "horario_funcionamento",
                  "telefone", "responsavel", "ativo", "latitude", "longitude"]
        for campo in campos:
            if campo in dados:
                setattr(ep, campo, dados[campo])
        db.session.commit()
        return {"mensagem": "Ecoponto atualizado", "ecoponto": ep.to_dict()}, 200

    def desativar(self, ecoponto_id: int) -> tuple[dict, int]:
        ep = Ecoponto.query.get_or_404(ecoponto_id)
        ep.ativo = False
        db.session.commit()
        return {"mensagem": "Ecoponto desativado"}, 200

    def mapa_url(self, latitude: float = None, longitude: float = None) -> dict:
        url = mapa_service.mapa_ecopontos_url(latitude, longitude)
        return {"url_mapa": url}


class NotificacaoService:

    def listar_por_bairro(self, bairro: str) -> list:
        notifs = NotificacaoBairro.query.filter(
            NotificacaoBairro.bairro.ilike(f"%{bairro}%"),
            NotificacaoBairro.data_coleta >= datetime.utcnow()
        ).order_by(NotificacaoBairro.data_coleta).all()
        return [n.to_dict() for n in notifs]

    def criar_calendario(self, dados: dict) -> tuple[dict, int]:
        notif = NotificacaoBairro(
            bairro=dados["bairro"],
            data_coleta=datetime.fromisoformat(dados["data_coleta"]),
            turno=dados.get("turno"),
            descricao=dados.get("descricao"),
        )
        db.session.add(notif)

        # Notifica cidadãos do bairro
        cidadaos = Usuario.query.filter(
            Usuario.bairro.ilike(f"%{dados['bairro']}%"),
            Usuario.tipo == TipoUsuario.CIDADAO,
            Usuario.ativo == True,
        ).all()

        for cidadao in cidadaos:
            n = Notificacao(
                usuario_id=cidadao.id,
                titulo="📅 Coleta no seu bairro!",
                mensagem=f"Haverá coleta seletiva em {dados['bairro']} em {notif.data_coleta.strftime('%d/%m/%Y')} ({dados.get('turno', 'horário a confirmar')})",
                tipo="bairro",
                referencia_id=notif.id,
            )
            db.session.add(n)

        db.session.commit()
        return {"mensagem": f"Calendário criado e {len(cidadaos)} cidadãos notificados", "notificacao": notif.to_dict()}, 201

    def listar_usuario(self, usuario_id: int, apenas_nao_lidas: bool = False) -> list:
        query = Notificacao.query.filter_by(usuario_id=usuario_id)
        if apenas_nao_lidas:
            query = query.filter_by(lida=False)
        notifs = query.order_by(Notificacao.criado_em.desc()).limit(50).all()
        return [n.to_dict() for n in notifs]

    def marcar_lida(self, notificacao_id: int, usuario_id: int) -> tuple[dict, int]:
        notif = Notificacao.query.get_or_404(notificacao_id)
        if notif.usuario_id != usuario_id:
            return {"erro": "Sem permissão"}, 403
        notif.lida = True
        db.session.commit()
        return {"mensagem": "Notificação marcada como lida"}, 200

    def marcar_todas_lidas(self, usuario_id: int) -> tuple[dict, int]:
        Notificacao.query.filter_by(usuario_id=usuario_id, lida=False).update({"lida": True})
        db.session.commit()
        return {"mensagem": "Todas as notificações marcadas como lidas"}, 200


ecoponto_service = EcopontoService()
notificacao_service = NotificacaoService()
