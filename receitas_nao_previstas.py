# receitas-nao-previstas

def receitas_nao_previstas_sql(entidade = 1, ano = 2022):
    sql = f"""
            SELECT 
                'receitas-nao-previstas' AS tipo_registro,
                MD5(CONCAT(recnaoprev.ano_exerc, recnaoprev.i_entidades, recnaoprev.natureza, recnaoprev.organograma)) as HASH,
                JSON_OBJECT(
                    'idIntegracao', MD5(CONCAT(recnaoprev.ano_exerc, recnaoprev.i_entidades, recnaoprev.natureza, recnaoprev.organograma)),
                    'content', 				                  
                    JSON_OBJECT(
                                'natureza', JSON_OBJECT('id', CAST(recnaoprev.natureza AS SIGNED)),							
                                'organograma', JSON_OBJECT('id', CAST(recnaoprev.organograma AS SIGNED)),
                                'exercicio', recnaoprev.ano_exerc							
                            )
                ) AS js 
            FROM (select receitas.ano_exerc, 
                         receitas.i_entidades,
                
                        (SELECT max(reg.id)
                            FROM registro_lotes reg
                            WHERE reg.tipo_registro = 'naturezas-receitas'
                                    AND reg.id IS NOT NULL
                                AND reg.json_store->>'$.content.numero' = 
                                        LEFT(if(substr(i_rubricas,1,1) = '4', substr(receitas.i_rubricas,2, length(receitas.i_rubricas)-1), receitas.i_rubricas), 14)
                                AND reg.json_store->>'$.content.configuracao.id' = 
                                (SELECT cast(max(reg.id) AS SIGNED)
                                    FROM registro_lotes reg			  	 		 
                                    WHERE reg.tipo_registro = 'configuracoes-naturezas-receitas'
                                        AND reg.json_store->>'$.content.descricao' = 'Portaria da Receita - {ano}')) AS 'natureza',

                        LEFT(if(substr(i_rubricas,1,1) = '4', substr(receitas.i_rubricas,2, length(receitas.i_rubricas)-1), receitas.i_rubricas), 14) AS 'rub',       
                        receitas.i_rubricas,
                
                        (SELECT cast(registro_lotes.id AS SIGNED)
                                FROM registro_lotes 			  	 		 
                                WHERE registro_lotes.tipo_registro = 'organogramas' 
                                    AND registro_lotes.json_store->>'$.content.numero' = 
                                    concat(LPAD(receitas.i_orgaos, 2, '0'),LPAD(receitas.i_unidades, 3,'0')) 
                                    AND registro_lotes.json_store->>'$.content.configuracao.id' = 
                                    CAST((SELECT max(reg.json_store->>'$.content.id')
                                            FROM registro_lotes reg
                                            WHERE reg.tipo_registro = 'configuracoes-organogramas'
                                                AND reg.json_store->>'$.content.descricao' LIKE '%{ano}%') AS SIGNED)) AS 'organograma',

                        sum(receitas.valor) as metaFinanceira
                    from receitas
                  where i_rubricas not like '9%'
                        and i_rubricas not like '49%'
                        AND receitas.ano_exerc = {ano}
            group by receitas.ano_exerc, receitas.i_entidades, receitas.i_rubricas, organograma
            having metaFinanceira = 0 ) recnaoprev 
            WHERE NOT EXISTS(SELECT 1
					           FROM registro_lotes reg
						      WHERE reg.json_store->>'$.content.natureza.id' = recnaoprev.natureza 
								    AND reg.json_store->>'$.content.organograma.id' = recnaoprev.organograma)  """
    return sql