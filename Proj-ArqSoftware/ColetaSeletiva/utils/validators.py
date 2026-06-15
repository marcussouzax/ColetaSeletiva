# utils/validators.py
import re
from datetime import datetime


def validar_email(email: str) -> bool:
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email))


def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[i]):
            return False
    return True


def validar_data_futura(data_str: str) -> tuple[bool, str]:
    try:
        data = datetime.fromisoformat(data_str)
        if data <= datetime.utcnow():
            return False, "A data deve ser futura"
        return True, ""
    except ValueError:
        return False, "Formato de data inválido. Use ISO 8601 (ex: 2025-12-31T08:00:00)"


def validar_coordenadas(lat: float, lng: float) -> bool:
    return -90 <= lat <= 90 and -180 <= lng <= 180


def validar_campos_obrigatorios(dados: dict, campos: list) -> list:
    """Retorna lista de campos faltantes"""
    return [c for c in campos if not dados.get(c)]


TIPOS_MATERIAL_VALIDOS = {"plastico", "papel", "vidro", "metal", "eletronico", "organico", "misto"}


def validar_materiais(materiais: list) -> tuple[bool, str]:
    for mat in materiais:
        if "tipo" not in mat:
            return False, "Cada material deve ter o campo 'tipo'"
        if mat["tipo"] not in TIPOS_MATERIAL_VALIDOS:
            return False, f"Tipo inválido: {mat['tipo']}. Válidos: {', '.join(TIPOS_MATERIAL_VALIDOS)}"
        if "quantidade_kg" in mat and mat["quantidade_kg"] is not None:
            if not isinstance(mat["quantidade_kg"], (int, float)) or mat["quantidade_kg"] < 0:
                return False, "quantidade_kg deve ser um número positivo"
    return True, ""
