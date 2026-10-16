# deducoes-receitas

def deducoes_receitas (entidade = 1, ano = 2022):
    sql = f"""
            SELECT 
                'deducoes-receitas' AS tipo_registro,
                MD5(CONCAT(deducao.descricao, deducao.tipo )) as HASH,
                JSON_OBJECT(
                        'idIntegracao', MD5(CONCAT(deducao.descricao, deducao.tipo )),
                            'content', 				                  
                            JSON_OBJECT(                       
                                        'descricao', deducao.descricao,
                                        'tipo', deducao.tipo
                            )
                    ) AS js 
            FROM (SELECT 
                        tipo_deducao.descricao AS 'descricao',
                        case tipo_deducao.tipo_stn
                        when 1 then 'RENUNCIA'
                        when 2 then 'RESTITUICOES'
                        when 3 then 'DESCONTOS_CONCEDIDOS'
                        when 5 then 'FUNDEB'
                        when 6 then 'COMPENSACOES'
                        when 8 then 'RETIFICACOES'
                        when 9 then 'OUTRAS_DEDUCOES'
                        else 'OUTRAS_DEDUCOES'
                        END AS 'tipo'
                FROM tipo_deducao 
            WHERE tipo_deducao.i_entidades = {entidade} 
                  AND tipo_deducao.ano_exerc = {ano} ) AS deducao
            WHERE NOT EXISTS(SELECT 1 
                               FROM registro_lotes 
                              WHERE registro_lotes.tipo_registro = 'deducoes-receitas'
                                    AND registro_lotes.json_store->>'$.content.descricao' = deducao.descricao
                                    AND (registro_lotes.json_store->>'$.content.tipo.key' = deducao.tipo OR 
                                         registro_lotes.json_store->>'$.content.tipo' = deducao.tipo)	
                                    AND registro_lotes.id IS NOT NULL ) """
    return sql
    