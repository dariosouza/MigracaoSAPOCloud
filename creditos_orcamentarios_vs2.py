

def ratear_anulacao(somas, subtracoes, ano_exerc):

    resultado = []

    indice_subtracao = 0

    for soma in somas:

        valor_soma = soma["valor"]

        valor_restante_soma = valor_soma

        origens = []

        while (
            valor_restante_soma > 0
            and indice_subtracao < len(subtracoes)
        ):

            sub = subtracoes[indice_subtracao]

            valor_disponivel = sub["valor_restante"]

            valor_rateado = min(
                valor_restante_soma,
                valor_disponivel
            )

            origens.append({

                "tipo": "DESPESA",

                "valor": float(valor_rateado),

                "origem": {
                    "id": sub["origem"]
                },

                "despesa": {
                    "id": sub["despesa"]
                },

                "recursos": [
                    {
                        "valor": float(valor_rateado),

                        "recurso": {
                            "id": sub["recurso"]
                        }
                    }
                ]
            })

            valor_restante_soma -= valor_rateado

            sub["valor_restante"] -= valor_rateado

            if sub["valor_restante"] == 0:
                indice_subtracao += 1

        # ------------------------------------------------------
        # VALIDA SE A DESPESA FOI TOTALMENTE RATEADA
        # ------------------------------------------------------

        if valor_restante_soma > 0:

            raise ValueError(
                f"Não foi possível ratear a despesa "
                f"{soma['despesa']}. "
                f"Valor restante: {valor_restante_soma}"
            )

        resultado.append({

            "i_movto_supl": soma["i_movto_supl"],

            "via": soma["via"],

            "tipo": "DESPESA",

            "valor": float(valor_soma),

            "despesa": {
                "id": soma["despesa"]
            },

            "origens": origens,

            "recursos": [
                {
                    "valor": float(valor_soma),

                    "recurso": {
                        "id": soma["recurso"]
                    }
                }
            ],

            "exercicio": ano_exerc,

            "finalidade": obter_finalidade(soma["via"]),

            "validaSaldo": False,

            "desconsideraLimite": False
        })

    return resultado





def processar_superavit(somas, ano_exerc):

    resultado = []

    for soma in somas:

        valor = soma["valor"]

        resultado.append({

            "i_movto_supl": soma["i_movto_supl"],

            "via": soma["via"],

            "tipo": "DESPESA",

            "valor": float(valor),

            "despesa": {
                "id": soma["despesa"]
            },

            "origens": [
                {
                    "tipo": "DESPESA",

                    "valor": float(valor),

                    "origem": {
                        "id": soma["origem"]
                    },

                    "despesa": {
                        "id": soma["despesa"]
                    },

                    "recursos": [
                        {
                            "valor": float(valor),

                            "recurso": {
                                "id": soma["recurso"]
                            }
                        }
                    ]
                }
            ],

            "recursos": [
                {
                    "valor": float(valor),

                    "recurso": {
                        "id": soma["recurso"]
                    }
                }
            ],

            "exercicio": ano_exerc,

            "finalidade": obter_finalidade(soma["via"]),

            "validaSaldo": False,

            "desconsideraLimite": False
        })

    return resultado




def processar_excesso_arrecadacao(somas, ano_exerc):

    resultado = []

    for soma in somas:

        valor = soma["valor"]

        resultado.append({

            "i_movto_supl": soma["i_movto_supl"],

            "via": soma["via"],

            "tipo": "DESPESA",

            "valor": float(valor),

            "despesa": {
                "id": soma["despesa"]
            },

            "origens": [
                {
                    "tipo": "DESPESA",

                    "valor": float(valor),

                    "origem": {
                        "id": soma["origem"]
                    },

                    "despesa": {
                        "id": soma["despesa"]
                    },

                    "recursos": [
                        {
                            "valor": float(valor),

                            "recurso": {
                                "id": soma["recurso"]
                            }
                        }
                    ]
                }
            ],

            "recursos": [
                {
                    "valor": float(valor),

                    "recurso": {
                        "id": soma["recurso"]
                    }
                }
            ],

            "exercicio": ano_exerc,

            "finalidade": obter_finalidade(soma["via"]),

            "validaSaldo": False,

            "desconsideraLimite": False
        })

    return resultado


def obter_finalidade(via):

    if via == "ABERTURA_CREDITO_ADICIONAL_ESPECIAL":
        return "Pela abertura de crédito Especial"

    elif via == "ABERTURA_CREDITO_ADICIONAL_SUPLEMENTAR":
        return "Pela abertura de crédito Suplementar"

    return None