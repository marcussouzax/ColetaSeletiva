# Coleta Seletiva

Sistema web desenvolvido para incentivar e gerenciar a coleta seletiva de resíduos, permitindo o cadastro de usuários, localização de pontos de coleta e sistema de pontuação para estimular práticas sustentáveis.

## Objetivo

O projeto foi desenvolvido com o propósito de promover a conscientização ambiental e facilitar o descarte correto de resíduos recicláveis por meio de uma plataforma simples e acessível.

## Tecnologias Utilizadas

- Python
- Flask
- PostgreSQL
- Redis
- JWT Authentication
- HTML
- CSS
- JavaScript
- Google Maps API

## Funcionalidades

- Cadastro e autenticação de usuários
- Controle de acesso utilizando JWT
- Consulta de pontos de coleta
- Sistema de pontuação por descarte
- Integração com mapas para localização de ecopontos
- Envio de notificações por e-mail
- Gerenciamento de dados através de banco de dados relacional

## Estrutura do Projeto

```text
ColetaSeletiva/
├── instance/
├── models/
├── routes/
├── services/
├── static/
├── templates/
├── utils/
├── .env.example
├── app.py
├── config.py
├── extensions.py
├── models.py
├── requirements.txt
├── seed.py
└── verificar.py
```

## Instalação

### Clonar o repositório

```bash
git clone https://github.com/seu-usuario/coletaseletiva.git
cd coletaseletiva
```

### Criar ambiente virtual

```bash
python -m venv venv
```

### Ativar ambiente virtual

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### Instalar dependências

```bash
pip install -r requirements.txt
```

### Configurar variáveis de ambiente

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Preencha as credenciais necessárias no arquivo `.env`.

### Executar o projeto

```bash
python app.py
```

## Banco de Dados

O projeto utiliza PostgreSQL como banco de dados principal.

Caso necessário, utilize o arquivo `seed.py` para popular o banco com dados iniciais.

## Segurança

As credenciais e chaves de acesso não são armazenadas no repositório. Utilize o arquivo `.env.example` como referência para configuração do ambiente.

## Projeto Acadêmico

Projeto desenvolvido para a disciplina de Arquitetura de Software, aplicando conceitos de organização em camadas, separação de responsabilidades e boas práticas de desenvolvimento web.

## Autor

**Marcus Souza**
