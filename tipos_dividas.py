# tipos-dividas

def tipos_dividas(entidade = 1, ano = 2022):
    sql = f"""
            SELECT 
                'tipos-dividas' AS tipo_registro,
                MD5(CONCAT(tpdiv.descricao, tpdiv.tipo, tpdiv.complemento)) as HASH,	   
                JSON_OBJECT(
                    'idIntegracao', MD5(CONCAT(tpdiv.descricao, tpdiv.tipo, tpdiv.complemento)),     
                        'content',					 	                  
                            JSON_OBJECT(					 	  
                                'tipo', tpdiv.tipo,
                                'descricao', tpdiv.descricao,
                                'complemento', tpdiv.complemento
                            )
                    ) AS js
            FROM (SELECT 	  
                        tpc.descricao as descricao,
                        COALESCE(if(tpc.descricao like '%mobiliária%' or tpc.descricao like '%título%', 'DIVIDA_MOBILIARIA', NULL), 
                                    if(tpc.descricao like '%arrendamento%' or tpc.descricao like '%mercantil%' or tpc.descricao like '%leasing%',
                                        'ARRENDAMENTO_MERCANTIL_LEASING', NULL),					
                                    if(((tpc.descricao like '%antecipação%' and tpc.descricao like '%rec%') OR 
                                        (tpc.descricao like '%antecipações%' and tpc.descricao like '%rec%') OR
                                        tpc.descricao like '%(ARO)%' or
                                    tpc.descricao like '%A.R.O%' or 
                                    tpc.descricao like 'ARO %' or 
                                    tpc.descricao like '% ARO'), 'ARO', NULL),
                                if(tpc.descricao like '%empréstimo%' or
                                    tpc.descricao like '%abertura de crédito%' or
                                    tpc.descricao like '%operações de crédito%' or
                                    tpc.descricao like '%operação de crédito%', 'EMPRESTIMO', NULL),
                                if(tpc.descricao like '%financiamento%' or
                                    tpc.descricao like '%financ%', 'FINANCIAMENTO', NULL),
                                if(tpc.descricao like '%recebimento antecipado%', 'RECEBIMENTO_ANTECIPADO_VALORES', NULL),
                                'CONFISSAO_DIVIDA') AS 'tipo',                                                                           
                        if(tpc.tipo_contrato = 'E', 'EXTERNO','INTERNO') as complemento 
                    FROM tipos_compromissos tpc join
                        (select i_plano_contas 
                            from parametros 
                            where parametros.ano_exerc = {ano} 
                                    and parametros.i_entidades = {entidade}) as param on tpc.i_plano_contas = param.i_plano_contas 
                    where tpc.i_entidades = {entidade}           
                            and tpc.classificacao = 'D'
                            and descricao NOT LIKE '%Precatórios%'
                    GROUP BY descricao, tipo, complemento) AS tpdiv 
            WHERE NOT EXISTS(SELECT 1 		
                               FROM registro_lotes reg
                              WHERE reg.tipo_registro = 'tipos-dividas' 
                                     AND (reg.JSON_store->>'$.content.tipo.key' = tpdiv.tipo OR 
                                          reg.JSON_store->>'$.content.tipo' = tpdiv.tipo) 
                                     AND (reg.JSON_store->>'$.content.complemento.key' = tpdiv.complemento OR 
                                          reg.JSON_store->>'$.content.complemento' = tpdiv.complemento)
                                     AND  reg.JSON_store->>'$.content.descricao' = tpdiv.descricao) """
    return sql
    