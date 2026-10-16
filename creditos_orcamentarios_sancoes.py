# creditos-orcamentarios-sancoes

def creditos_orcamentarios_sancoes_sql (entidade = 1, ano = 2022):
    sql = f"""
            SELECT 
                'creditos-orcamentarios-sancoes' AS tipo_registro,
                MD5(CONCAT(sancoes.id, sancoes.data_suplementacao, sancoes.ano_exerc)) as HASH,
                JSON_OBJECT(
                        'idIntegracao', MD5(CONCAT(sancoes.id, sancoes.data_suplementacao, sancoes.ano_exerc)),
                        'content', 				                  
                        JSON_OBJECT(
                                                        'dataSancao', sancoes.data_suplementacao,							
                                'atoAutorizativo', JSON_OBJECT('id', CAST(sancoes.idAtoAutorizativo AS SIGNED) ),
                                'atoAbertura', JSON_OBJECT('id', CAST(sancoes.idAtoAbertura AS SIGNED)),
                                                        'creditos', JSON_ARRAY(JSON_OBJECT('id', cast(sancoes.id AS SIGNED))),
                                                        'exercicio', sancoes.ano_exerc
                        )
                        ) AS js,
                        JSON_OBJECT('creditos', sancoes.id) AS refdados 	
                FROM (SELECT  
                        registro_lotes.id,
                        suplement.i_suplementacoes,
                        suplement.data_suplementacao,
                        suplement.ano_exerc,
                        
                        (SELECT regl.id
                                FROM registro_lotes regl 
                                WHERE regl.tipo_registro = 'atos' 
                                                AND regl.json_store->>'$.content.numero' = concat(left(suplement.fundamento,length(suplement.fundamento)-2))
                                                AND regl.json_store->>'$.content.tipo.descricao' = 'DECRETO') AS idAtoAbertura,
                                                
                        (SELECT regl.id
                        FROM registro_lotes regl 
                        WHERE regl.tipo_registro = 'atos' 
                                                AND regl.json_store->>'$.content.numero' = concat(left(suplement.i_leis,length(suplement.i_leis)-2))
                                                AND regl.json_store->>'$.content.tipo.descricao' = 'LEI') AS idAtoAutorizativo
									  		 		 
                   FROM registro_lotes,
                                        suplement	 
                        WHERE registro_lotes.tipo_registro = 'creditos-orcamentarios' 
                                        AND Id IS NOT NULL
                                        AND suplement.i_entidades = {entidade} 
                                        AND suplement.ano_exerc = {ano}		 			 
                                        AND registro_lotes.refdados->>'$.i_suplementacoes' = suplement.i_suplementacoes
                                        AND suplement.data_suplementacao IS NOT NULL ) AS sancoes
                                        WHERE NOT EXISTS(SELECT 1
                                                           FROM registro_lotes reg
                                                          WHERE reg.tipo_registro = 'creditos-orcamentarios-sancoes'
                                                                AND reg.id IS NOT NULL	
                                                                AND coalesce(JSON_store->>'$.content.creditos[0].id',
                                                                JSON_store->>'$.content.creditos[0].credito.id') = sancoes.id)
                                ORDER BY sancoes.data_suplementacao	
                """
            
#     sql = f"""
#             SELECT 
#             'creditos-orcamentarios-sancoes' AS tipo_registro,
#             MD5(reg.id) as HASH,
#             JSON_OBJECT(
#                 'idIntegracao', MD5(reg.id),
#                 'idGerado', JSON_OBJECT('id', cast(reg.id AS SIGNED)),
#                 'content', JSON_OBJECT('exercicio', cast(json_store->>'$.content.exercicio' AS SIGNED))
#             ) AS js 
#         FROM registro_lotes reg
#        WHERE reg.tipo_registro = 'creditos-orcamentarios-sancoes'
#              AND reg.id IS NOT NULL
#              AND reg.json_store->>'$.content.exercicio' = {ano}
#         """
    return sql
    