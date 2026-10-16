from decimal import Decimal
import hashlib
import json


def ratear_suplementacao(conn, i_entidades, ano_exerc, i_suplementacoes):

    sql = """
        SELECT
		'creditos-orcamentarios' AS tipo_registro,
        suplement.i_suplementacoes,
        MD5(CONCAT(suplement.i_entidades, 
                        movto_supl.ano_exerc,
                        movto_supl.i_despesas, 
                        movto_supl.i_suplementacoes, 
                        suplement.data_suplementacao)) as HASH,                  
        movto_supl.i_movto_supl,
        CASE suplement.ementa
            WHEN 58 THEN 'ABERTURA_CREDITO_ADICIONAL_SUPLEMENTAR'
            WHEN 60 THEN 'ABERTURA_CREDITO_ADICIONAL_ESPECIAL'
        END AS via,
        busca_id_despesa(
            300488,
            suplement.i_entidades,
            movto_supl.ano_exerc,
            movto_supl.i_despesas
        ) AS despesa,
        busca_id_recurso(
            movto_supl.i_entidades,
            movto_supl.i_recursos,
            'N'
        ) AS recurso_principal,
        busca_id_recurso(
            movto_supl.i_entidades,
            movto_supl.i_recursos,
            IF(movto_supl.origem_recurso IN (2), 'S', 'N')
        ) AS recurso,
        movto_supl.valor AS valor,
        suplement.ementa AS ementa,
        suplement.ano_exerc AS ano,
        movto_supl.tipo_movimento,
        movto_supl.origem_recurso,
        busca_id_origem_despesa(
            movto_supl.i_entidades,
            movto_supl.ano_exerc,
            movto_supl.i_movto_supl
        ) AS origem,
        JSON_OBJECT('i_entidades', suplement.i_entidades,
                            'ano_exerc', movto_supl.ano_exerc,
                            'i_movto_supl', movto_supl.i_movto_supl,
                            'i_suplementacoes', suplement.i_suplementacoes) AS refdados
        FROM suplement,
             movto_supl

        WHERE suplement.i_entidades = %s
          AND suplement.ano_exerc = %s
          AND suplement.i_suplementacoes = %s

          AND suplement.i_entidades = movto_supl.i_entidades
          AND suplement.ano_exerc = movto_supl.ano_exerc
          AND suplement.i_suplementacoes = movto_supl.i_suplementacoes
          AND suplement.data_suplementacao IS NOT NULL
          AND NOT EXISTS(SELECT 1
                           FROM registro_lotes 
                          WHERE registro_lotes.tipo_registro = 'creditos-orcamentarios'
                                AND registro_lotes.refdados->>'$.i_entidades' = suplement.i_entidades
                                AND registro_lotes.refdados->>'$.ano_exerc' = suplement.ano_exerc
                                AND registro_lotes.refdados->>'$.i_suplementacoes' = suplement.i_suplementacoes
                                AND registro_lotes.id IS NOT NULL)
        ORDER BY movto_supl.i_movto_seq
    """
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        sql,
        (
            i_entidades,
            ano_exerc,
            i_suplementacoes
        )
    )
    movimentos = cursor.fetchall()
    cursor.close()        
    
    tipo_origem = 'N'    
    for mov in movimentos:
        if mov["origem_recurso"] == 1:        
           tipo_origem = 'S'
        if mov["origem_recurso"] in (2,3):
            tipo_origem = 'N'                
    
    if tipo_origem == 'S':
        return processar_rateio_ordenado(movimentos, ano_exerc)
    if tipo_origem == 'N':     
        return processar_superavit_excesso (movimentos, ano_exerc)
    
    return None
    
def processar_superavit_excesso (movimentos, ano_exer):
    
    resultado = []    
    for movimento in movimentos:        
        if movimento["origem_recurso"] in (2,3): #2-Superávit financeiro, 3-Excesso de arrecadação
            item = {            
                "content": {
                    "via": movimento["via"],
                    "tipo": "DESPESA",
                    "exercicio": ano_exer,
                    "finalidade": "Pela abertura de crédito Especial " + str(movimento["i_suplementacoes"]),
                    "validaSaldo": False,
                    "desconsideraLimite": False,
                    "valor": Decimal(str(movimento["valor"])),
                    "despesa": { 
                        "id": movimento["despesa"] 
                    },
                    "recursos": [
                        {
                            "valor": Decimal(str(movimento["valor"])),
                            "recurso": {
                                "id": movimento["recurso_principal"]
                            }
                        }
                    ],
                    "origens":[{                    
                        "tipo": "DESPESA",
                        "valor": Decimal(str(movimento["valor"])),
                        "origem": {
                            "id": movimento["origem"]
                        },
                        "recursos": [
                            {
                                "valor": Decimal(str(movimento["valor"])),
                                "recurso": {
                                    "id": movimento["recurso"]
                                }
                            }
                        ]
                    }]         
                },
                "idIntegracao": movimento["HASH"],
                "refdados": json.loads(movimento["refdados"])
            }
            resultado.append(item)
    return resultado
    
def processar_rateio(movimentos, ano_exerc):

    somas = []
    subtracoes = []
    # ==========================================================
    # SEPARA OS MOVIMENTOS
    # ==========================================================
    for movimento in movimentos:
        item = {
            "i_movto_supl": movimento["i_movto_supl"],
            "via": movimento["via"],
            "despesa": movimento["despesa"],
            "recurso": movimento["recurso"],
            "valor": Decimal(str(movimento["valor"])),
            "tipo_movimento": movimento["tipo_movimento"],
            "origem": movimento["origem"]
        }
        if movimento["tipo_movimento"] == '1':            
            somas.append(item)
        elif movimento["tipo_movimento"] == '2':
            item["valor_restante"] = Decimal(
                str(movimento["valor"])
            )
            subtracoes.append(item)
    # ==========================================================
    # RESULTADO
    # ==========================================================
    resultado = []
    indice_subtracao = 0
    # ==========================================================
    # PROCESSA CADA TIPO 1
    # ==========================================================
    for soma in somas:
        valor_soma = soma["valor"]
        valor_restante_soma = valor_soma
        origens = []
        # ------------------------------------------------------
        # CONSOME AS SUBTRAÇÕES
        # ------------------------------------------------------
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
            # --------------------------------------------------
            # CRIA A ORIGEM
            # --------------------------------------------------
            origem = {
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
            }
            origens.append(origem)
            # --------------------------------------------------
            # ATUALIZA OS SALDOS
            # --------------------------------------------------
            valor_restante_soma -= valor_rateado
            sub["valor_restante"] -= valor_rateado
            # --------------------------------------------------
            # SE ACABOU A SUBTRAÇÃO
            # --------------------------------------------------
            if sub["valor_restante"] == 0:
                indice_subtracao += 1
        # ------------------------------------------------------
        # CRIA O MOVIMENTO PRINCIPAL
        # ------------------------------------------------------
        resultado.append({
            "content": {
                #"i_movto_supl": soma["i_movto_supl"],
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
                "finalidade": (
                    "Pela abertura de crédito Especial " + str(movimento["i_suplementacoes"])
                    if soma["via"] ==
                    "ABERTURA_CREDITO_ADICIONAL_ESPECIAL"
                    else
                    "Pela abertura de crédito Suplementar " + str(movimento["i_suplementacoes"]) 
                ),
                "validaSaldo": False,
                "desconsideraLimite": False
            },
            "idIntegracao":  hashlib.md5(  (str(movimento["i_movto_supl"]) + str(ano_exerc) + str(float(valor_rateado)) + str(soma["recurso"])  ).encode("utf-8")).hexdigest(),
            "refdados": json.loads(movimento["refdados"])
        })                
    return resultado

def processar_rateio_ordenado(movimentos, ano_exerc):
    somas = []
    subtracoes = []
    # ==========================================================
    # SEPARA OS MOVIMENTOS
    # ==========================================================
    for movimento in movimentos:
        item = {
            "i_movto_supl": movimento["i_movto_supl"],
            "i_suplementacoes": movimento["i_suplementacoes"],
            "via": movimento["via"],
            "despesa": movimento["despesa"],
            "recurso": movimento["recurso"],
            "valor": Decimal(str(movimento["valor"])),
            "tipo_movimento": movimento["tipo_movimento"],
            "origem": movimento["origem"],
            "refdados": movimento["refdados"]
        }
        if movimento["tipo_movimento"] == '1':
            somas.append(item)
        elif movimento["tipo_movimento"] == '2':
            item["valor_restante"] = Decimal(
                str(movimento["valor"])
            )
            subtracoes.append(item)
    # ==========================================================
    # RESULTADO
    # ==========================================================
    resultado = []
    indice_subtracao = 0
    # ==========================================================
    # PROCESSA CADA TIPO 1
    # ==========================================================
    for soma in somas:
        valor_soma = soma["valor"]
        valor_restante_soma = valor_soma
        # ======================================================
        # DICIONÁRIO PARA CONSOLIDAR AS ORIGENS
        # ======================================================
        origens_dict = {}
        # ------------------------------------------------------
        # CONSOME AS SUBTRAÇÕES
        # ------------------------------------------------------
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
            # ==================================================
            # CONSOLIDA PELA DESPESA
            # ==================================================
            despesa_id = sub["despesa"]
            if despesa_id not in origens_dict:
                origens_dict[despesa_id] = {
                    "tipo": "DESPESA",
                    "valor": Decimal("0"),
                    "origem": {
                        "id": sub["origem"]
                    },
                    "despesa": {
                        "id": despesa_id
                    },
                    "recursos": {}
                }
            origem = origens_dict[despesa_id]
            # --------------------------------------------------
            # SOMA O VALOR DA DESPESA
            # --------------------------------------------------
            origem["valor"] += valor_rateado
            # --------------------------------------------------
            # CONSOLIDA O RECURSO
            # --------------------------------------------------
            recurso_id = sub["recurso"]
            if recurso_id not in origem["recursos"]:
                origem["recursos"][recurso_id] = Decimal("0")
            origem["recursos"][recurso_id] += valor_rateado
            # --------------------------------------------------
            # ATUALIZA OS SALDOS
            # --------------------------------------------------
            valor_restante_soma -= valor_rateado
            sub["valor_restante"] -= valor_rateado
            # --------------------------------------------------
            # SE ACABOU A SUBTRAÇÃO
            # --------------------------------------------------
            if sub["valor_restante"] == 0:
                indice_subtracao += 1
        # ======================================================
        # TRANSFORMA O DICIONÁRIO DE ORIGENS NO JSON FINAL
        # ======================================================
        origens = []
        for origem in origens_dict.values():
            # --------------------------------------------------
            # PEGA O RECURSO COM MAIOR VALOR
            # --------------------------------------------------
            recurso_maior = max(
                origem["recursos"].items(),
                key=lambda x: x[1]
            )
            recurso_id = recurso_maior[0]
            valor_recurso = origem["valor"]
            # -------------------------------------------------
            # MONTA A ORIGEM FINAL
            # --------------------------------------------------
            origens.append({
                "tipo": origem["tipo"],
                "valor": float(
                    origem["valor"]
                ),
                "origem": origem["origem"],
                "despesa": origem["despesa"],
                "recursos": [
                    {
                        "valor": float(
                            valor_recurso
                        ),
                        "recurso": {
                            "id": recurso_id
                        }
                    }
                ]
            })
        # ======================================================
        # VALIDA SE O RATEIO FOI COMPLETO
        # ======================================================
        # if valor_restante_soma > 0:

        #     raise ValueError(
        #         f"Não foi possível ratear completamente "
        #         f"a despesa {soma['despesa']}. "
        #         f"Valor restante: {valor_restante_soma}"
        #     )
        # ======================================================
        # FINALIDADE
        # ======================================================
        if soma["via"] == (
            "ABERTURA_CREDITO_ADICIONAL_ESPECIAL"
        ):
            finalidade = (
                "Pela abertura de crédito Especial "
                + str(soma["i_suplementacoes"])
            )
        else:
            finalidade = (
                "Pela abertura de crédito Suplementar "
                + str(soma["i_suplementacoes"])
            )
        # ======================================================
        # MONTA O RESULTADO
        # ======================================================
        resultado.append({
            "content": {
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
                "finalidade": finalidade,
                "validaSaldo": False,
                "desconsideraLimite": False
            },
            "idIntegracao": hashlib.md5(
                (
                    str(soma["i_movto_supl"])
                    + str(ano_exerc)
                    + str(float(valor_soma))
                    + str(soma["recurso"])
                ).encode("utf-8")
            ).hexdigest(),

            "refdados": json.loads(
                soma["refdados"]
            )
        })
    return resultado

def processa_suplementacoes(conn = None, i_entidades = 1, ano_exerc = 2022, i_suplementacoes = 0):
   
    sql = f""" SELECT suplement.i_suplementacoes,
                      JSON_OBJECT('i_entidades', suplement.i_entidades,
                                  'ano_exerc', suplement.ano_exerc,
                                  'i_movto_supl', group_concat(distinct movto_supl.i_movto_supl),
                                  'i_suplementacoes', suplement.i_suplementacoes) AS refdados
                FROM suplement,
                     movto_supl
               WHERE suplement.i_entidades = {i_entidades} 
                     AND suplement.ano_exerc = {ano_exerc} 
                     #AND suplement.i_suplementacoes = {i_suplementacoes}
                     AND suplement.i_entidades = movto_supl.i_entidades
                     AND suplement.ano_exerc = movto_supl.ano_exerc
                     AND suplement.i_suplementacoes = movto_supl.i_suplementacoes
                     AND suplement.data_suplementacao IS NOT NULL
            GROUP BY suplement.i_entidades, suplement.ano_exerc, suplement.i_suplementacoes """
    
    createtable = """
                CREATE TEMPORARY TABLE creditos_arrecadacao (
                    tipo_registro varchar(120),
                    hash_v varchar(64),
                    json_store json,
                    json_refdados json      
                ); 
            """    
    ##############################
    cuexetbl =  conn.cursor()
    cuexetbl.execute(createtable)
    cuexetbl.close() 
    ##############################    
    
    credArra = []
    tmpCred = []
    cursor = conn.cursor()
    cursor.execute(sql)
    creditos = cursor.fetchall()        
    cursor.close()    
    ##############################
    curinsert = conn.cursor(dictionary=True)
    for row in creditos:
        credArra.append( ratear_suplementacao(conn, i_entidades, ano_exerc, row[0]) )
    for lista in credArra:
        for item in lista:
            refdados = item.pop("refdados", None)
            tmpCred.append(item)
            sqlinsert = """INSERT INTO  creditos_arrecadacao (tipo_registro, hash_v, json_store, json_refdados) values (%s, %s, %s, %s);"""
            curinsert.execute( sqlinsert,("creditos-orcamentarios", None, json.dumps(item, default=float), json.dumps(refdados) )) 
    curinsert.close()    
    return "select tipo_registro, hash_v, json_store, json_refdados from creditos_arrecadacao"
        