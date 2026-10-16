# origens-creditos-orcamentarios-exercicios

def origens_creditos_orcamentarios_exercicios_sql (entidade = 1, ano = 2022):
    sql = f"""
                SELECT 
                        orcrorexe.tipo_registro AS tipo_registro,
                        MD5(CONCAT(orcrorexe.tipo_registro, orcrorexe.id, orcrorexe.exercicio)) as HASH,
                        JSON_OBJECT(
                            'idIntegracao', MD5(CONCAT(orcrorexe.tipo_registro, orcrorexe.id, orcrorexe.exercicio)),
                            'content', 				                  
                            JSON_OBJECT('exercicio', orcrorexe.exercicio,
                                        'origemCreditoOrcamentario', JSON_OBJECT('id', CAST(orcrorexe.id AS SIGNED))
                                    )
                        ) AS js       
                FROM (SELECT 'origens-creditos-orcamentarios-exercicios' AS tipo_registro,
                                reg.id AS 'id',
                                {ano} AS exercicio
                        FROM registro_lotes reg
                        WHERE reg.tipo_registro = 'origens-creditos-orcamentarios'
                                AND reg.id IS NOT NULL) orcrorexe
                WHERE NOT EXISTS(SELECT 1
                                        FROM registro_lotes reg
                                        WHERE reg.tipo_registro = 'origens-creditos-orcamentarios-exercicios' 
                                            AND (reg.json_store->>'$.content.exercicio' = orcrorexe.exercicio OR 
                                                 reg.json_store->>'$.content.exercicio.ano' = orcrorexe.exercicio)
                                             AND reg.json_store->>'$.content.origemCreditoOrcamentario.id' = orcrorexe.id) 
            """
    return sql
    