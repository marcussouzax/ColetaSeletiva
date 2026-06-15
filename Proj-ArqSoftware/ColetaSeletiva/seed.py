"""
Script de seed para popular o banco com dados de exemplo.
Uso: python seed.py
"""
from app import create_app
from extensions import db
from models.usuario import Usuario, PontosConta, Beneficio, TipoUsuario
from models.ponto_coleta import Ecoponto, MaterialEcoponto
from datetime import datetime, timedelta


def seed():
    app = create_app()
    with app.app_context():
        print("Iniciando seed...")

        # Usuários
        usuarios_data = [
            {
                "nome": "Prefeitura EcoCidade",
                "email": "prefeitura@ecocidade.gov.br",
                "senha": "admin123",
                "tipo": TipoUsuario.PREFEITURA,
            },
            {
                "nome": "Cooperativa Verde Vida",
                "email": "cooperativa@verdevida.com.br",
                "senha": "coop123",
                "tipo": TipoUsuario.COOPERATIVA,
                "bairro": "Centro",
            },
            {
                "nome": "João Silva",
                "email": "joao@email.com",
                "senha": "cidadao123",
                "tipo": TipoUsuario.CIDADAO,
                "bairro": "Boa Vista",
                "telefone": "81999990001",
            },
            {
                "nome": "Maria Souza",
                "email": "maria@email.com",
                "senha": "cidadao123",
                "tipo": TipoUsuario.CIDADAO,
                "bairro": "Prado",
                "telefone": "81999990002",
            },
        ]

        for u_data in usuarios_data:
            if not Usuario.query.filter_by(email=u_data["email"]).first():
                u = Usuario(
                    nome=u_data["nome"],
                    email=u_data["email"],
                    tipo=u_data["tipo"],
                    bairro=u_data.get("bairro"),
                    telefone=u_data.get("telefone"),
                )
                u.set_senha(u_data["senha"])
                db.session.add(u)
                db.session.flush()
                if u.tipo == TipoUsuario.CIDADAO:
                    conta = PontosConta(usuario_id=u.id, saldo=150, total_acumulado=150)
                    db.session.add(conta)
                print(f" Usuário criado: {u.email}")

        # Ecopontos
        ecopontos_data = [
            {
                "nome": "Ecoponto Central",
                "endereco": "Av. Principal, 100",
                "bairro": "Centro",
                "latitude": -8.0476,
                "longitude": -34.877,
                "horario_funcionamento": "Seg-Sex 8h-17h, Sab 8h-12h",
                "materiais": ["plastico", "papel", "metal", "vidro"],
            },
            {
                "nome": "Ecoponto Boa Vista",
                "endereco": "Rua das Flores, 250",
                "bairro": "Boa Vista",
                "latitude": -8.0510,
                "longitude": -34.881,
                "horario_funcionamento": "Seg-Sex 7h-16h",
                "materiais": ["plastico", "papel", "eletronico"],
            },
            {
                "nome": "Ecoponto Prado",
                "endereco": "Praça da Liberdade, s/n",
                "bairro": "Prado",
                "latitude": -8.0440,
                "longitude": -34.874,
                "horario_funcionamento": "Seg-Sab 8h-18h",
                "materiais": ["plastico", "vidro", "metal", "organico"],
            },
        ]

        for ep_data in ecopontos_data:
            if not Ecoponto.query.filter_by(nome=ep_data["nome"]).first():
                ep = Ecoponto(
                    nome=ep_data["nome"],
                    endereco=ep_data["endereco"],
                    bairro=ep_data["bairro"],
                    latitude=ep_data["latitude"],
                    longitude=ep_data["longitude"],
                    horario_funcionamento=ep_data["horario_funcionamento"],
                )
                db.session.add(ep)
                db.session.flush()
                for tipo_mat in ep_data["materiais"]:
                    m = MaterialEcoponto(ecoponto_id=ep.id, tipo=tipo_mat)
                    db.session.add(m)
                print(f" Ecoponto criado: {ep.nome}")

        # Benefícios
        beneficios_data = [
            {"nome": "Passe de ônibus", "custo_pontos": 100, "categoria": "transporte",
             "descricao": "1 passagem de ônibus municipal", "quantidade_estoque": 500},
            {"nome": "Ingresso Teatro Municipal", "custo_pontos": 200, "categoria": "evento",
             "descricao": "Ingresso para espetáculos no Teatro Municipal", "quantidade_estoque": 50},
            {"nome": "Desconto 10% Feira Verde", "custo_pontos": 80, "categoria": "desconto",
             "descricao": "10% de desconto na Feira Orgânica Municipal", "quantidade_estoque": None},
            {"nome": "Mudas de plantas", "custo_pontos": 50, "categoria": "evento",
             "descricao": "Kit com 3 mudas do viveiro municipal", "quantidade_estoque": 200},
        ]

        for b_data in beneficios_data:
            if not Beneficio.query.filter_by(nome=b_data["nome"]).first():
                b = Beneficio(**b_data)
                db.session.add(b)
                print(f" Benefício criado: {b.nome}")

        db.session.commit()
        print("\n Seed concluído com sucesso!")
        print("\nCredenciais de acesso:")
        print("  Prefeitura:  prefeitura@ecocidade.gov.br / admin123")
        print("  Cooperativa: cooperativa@verdevida.com.br / coop123")
        print("  Cidadão 1:   joao@email.com / cidadao123")
        print("  Cidadão 2:   maria@email.com / cidadao123")


if __name__ == "__main__":
    seed()
