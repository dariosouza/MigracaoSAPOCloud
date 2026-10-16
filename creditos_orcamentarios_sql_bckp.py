# creditos-orcamentarios

def creditos_orcamentarios_sql (entidade = 1, ano = 2022, conn = None):
    sql = f"""
            SELECT 
                    'creditos-orcamentarios' AS tipo_registro,
                     MD5(CONCAT(suplement.i_entidades, movto_supl.ano_exerc, movto_supl.i_despesas, movto_supl.i_suplementacoes, suplement.data_suplementacao)) as HASH,                  
                    JSON_OBJECT(
                    'idIntegracao', MD5(CONCAT(suplement.i_entidades, movto_supl.ano_exerc, movto_supl.i_despesas, movto_supl.i_suplementacoes, suplement.data_suplementacao)),
                    'content', 	
                    JSON_MERGE_PRESERVE(	 		   		                  
                    JSON_OBJECT('desconsideraLimite', false,
                                    'tipo', 'DESPESA',
                                    'finalidade', 'Pela abertura de crédito Especial',
                                    'valor', movto_supl.valor,
                                    'validaSaldo', FALSE,
                                    'exercicio', movto_supl.ano_exerc,
                                    'despesa', JSON_OBJECT('id', busca_id_despesa(300488, suplement.i_entidades, movto_supl.ano_exerc, movto_supl.i_despesas) ),
                                    'recursos', JSON_ARRAY(JSON_OBJECT('recurso', JSON_OBJECT('id', busca_id_recurso(suplement.i_entidades, movto_supl.i_recursos, 'N')), 'valor', movto_supl.valor)),
                                    'via', ((case suplement.ementa
                                                    when 58 then 'ABERTURA_CREDITO_ADICIONAL_SUPLEMENTAR'
                                                    when 60 then 'ABERTURA_CREDITO_ADICIONAL_ESPECIAL'
                                                END))
                                        ),		  
                                        if(EXISTS(SELECT 1 FROM movto_supl mvexis
                                                    WHERE mvexis.i_entidades = suplement.i_entidades
                                                            AND mvexis.ano_exerc = movto_supl.ano_exerc
                                                            AND mvexis.i_suplementacoes = movto_supl.i_suplementacoes	
                                                            AND (mvexis.tipo_movimento = 2 OR (mvexis.tipo_movimento = 1 AND movto_supl.origem_recurso IN (2,3))) ), 
                                                            
                                                            JSON_OBJECT('origens',(SELECT JSON_ARRAYAGG(
                                                                                                    JSON_MERGE_PRESERVE(		
                                                                                                        JSON_OBJECT('tipo','DESPESA', 
                                                                                                                        'origem', JSON_OBJECT('id', busca_id_origem_despesa(mtosp.i_entidades, mtosp.ano_exerc, mtosp.i_movto_supl)  ),	 	 		  		  																						 		 																			 	 	 
                                                                                                                    'valor', mtosp.valor,
                                                                                                                    'recursos', JSON_ARRAY(JSON_OBJECT('recurso',JSON_OBJECT('id', busca_id_recurso(mtosp.i_entidades, mtosp.i_recursos, if(movto_supl.origem_recurso IN (2), 'S', 'N'))), 'valor', mtosp.valor))								    
                                                                                                        ),
                                                                                                        if(mtosp.tipo_movimento = 2, 
                                                                                                            JSON_OBJECT('despesa',JSON_OBJECT('id', busca_id_despesa(300488, mtosp.i_entidades, mtosp.ano_exerc, mtosp.i_despesas))),
                                                                                                            JSON_OBJECT()
                                                                                                        )
                                                                                                    )
                                                                                            ) AS js
                                                                                        FROM movto_supl mtosp
                                                                                        WHERE mtosp.i_entidades = suplement.i_entidades
                                                                                                AND mtosp.ano_exerc = movto_supl.ano_exerc
                                                                                                AND mtosp.i_suplementacoes = movto_supl.i_suplementacoes 
                                                                                                AND (mtosp.tipo_movimento = 2 OR (mtosp.tipo_movimento = 1 AND movto_supl.origem_recurso IN (2,3)))) ),
                                                                JSON_OBJECT() )																									  								
                            
                        )
                ) AS js,
                    movto_supl.i_recursos,
                    suplement.i_suplementacoes 
            FROM suplement,
                    movto_supl
            WHERE suplement.i_entidades = {entidade} 
                    AND suplement.ano_exerc = {ano}
                    #AND suplement.i_suplementacoes = 131
                    AND suplement.data_suplementacao IS NOT NULL
                    AND movto_supl.i_entidades = suplement.i_entidades 
                    AND movto_supl.ano_exerc = suplement.ano_exerc 
                    AND movto_supl.i_suplementacoes = suplement.i_suplementacoes 						
                    AND movto_supl.tipo_movimento	= 1 
                    AND (SELECT COUNT(*) 
                        FROM movto_supl movtsupl
                        WHERE movtsupl.i_entidades = suplement.i_entidades 
                                AND movtsupl.ano_exerc = suplement.ano_exerc 
                                AND movtsupl.i_suplementacoes = suplement.i_suplementacoes 
                                AND movtsupl.tipo_movimento = 1) = 1
                    /*AND movto_supl.origem_recurso = 3 
                    AND EXISTS(SELECT 1
                                    FROM registro_lotes reg
                                    WHERE reg.tipo_registro = 'creditos-orcamentarios' 
                                            AND reg.idIntegracao = 
                                            MD5(CONCAT(suplement.i_entidades, movto_supl.ano_exerc, movto_supl.i_despesas, movto_supl.i_suplementacoes, suplement.data_suplementacao))
                                            AND reg.id IS NULL)*/
        """
    # exclusão dos creditos orçamentários 
    # sql = f"""
    #             SELECT 
    #                     'creditos-orcamentarios' AS tipo_registro,
    #                     MD5(CONCAT(registro_lotes.id, registro_lotes.json_store->>'$.content.exercicio' )) as HASH,
    #                     JSON_OBJECT(
    #                     'idIntegracao', MD5(CONCAT(registro_lotes.id, registro_lotes.json_store->>'$.content.exercicio' )),
    #                     'idGerado', JSON_OBJECT('id', cast(registro_lotes.id AS SIGNED)),
    #                     'content', JSON_OBJECT('exercicio', cast(json_store->>'$.content.exercicio' AS SIGNED))
    #                 ) AS js 
    #             FROM registro_lotes 
    #             WHERE tipo_registro = 'creditos-orcamentarios' 
    #                     and id IS NOT NULL 
    #                     and json_store->>'$.content.exercicio' = 2022
    #             """    
                
    return sql
    