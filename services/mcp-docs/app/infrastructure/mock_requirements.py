_REQUIREMENTS = {
    "cuenta_ahorros": [
        "Contrato de cuenta de ahorros",
        "Formulario Conozca a su Cliente (KYC)",
        "Autorización de tratamiento de datos personales",
    ],
    "cuenta_corriente": [
        "Contrato de cuenta corriente",
        "Formulario Conozca a su Cliente (KYC)",
        "Declaración de origen de fondos",
        "Autorización de tratamiento de datos personales",
    ],
    "tarjeta_credito": [
        "Solicitud de tarjeta de crédito",
        "Formulario Conozca a su Cliente (KYC)",
        "Autorización de consulta al buró de crédito",
    ],
}


class MockProductRequirements:
    def documents_for(self, product: str) -> list[str] | None:
        return _REQUIREMENTS.get(product)
