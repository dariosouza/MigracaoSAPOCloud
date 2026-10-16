# dividas

def dividas (entidade = 1, ano = 2022):
    sql = f"""
            SELECT 
                'dividas' AS tipo_registro,
                MD5(CONCAT(dividas.i_entidades, dividas.i_contratos, dividas.exercicio)) as HASH,	  
                JSON_OBJECT(
                    'idIntegracao', MD5(CONCAT(dividas.i_entidades, dividas.i_contratos, dividas.exercicio)),     
                        'content',					 	                  
                            JSON_OBJECT(					 	  							                 
                                'ato', JSON_OBJECT('id', CAST(dividas.id_ato AS SIGNED)),
                                'data', dividas.data_assinatura,
                                'tipo', JSON_OBJECT('id', CAST(dividas.tipo AS SIGNED)),
                                'valor', dividas.valor,
                                    'credor', JSON_OBJECT('id', CAST(dividas.credor AS SIGNED)),
                                    'numero', dividas.numero,
                                    'exercicio', CAST(dividas.exercicio AS SIGNED),
                                    'especificacao', dividas.especificacao,
                                    'parcelas', (SELECT JSON_ARRAYAGG(
                                                                        JSON_OBJECT('numero', cp.numero_parcela,
                                                                                        'valorJuros', cp.juros,
                                                                                        'valorEncargos', cp.encargos,
                                                                                        'dataVencimento', cp.data_vencimento,
                                                                                        'valorPrincipal', cp.valor)) 																			
                                                        FROM(SELECT cp.numero_parcela,
                                                                        cp.juros,
                                                                        cp.encargos,
                                                                        cp.data_vencimento,
                                                                        cp.valor  
                                                                FROM contratos_parcelas cp
                                                                WHERE cp.i_entidades = dividas.i_entidades
                                                                        AND cp.i_contratos = dividas.i_contratos
                                                            UNION ALL 
                                                                SELECT 1 AS numero_parcela, 
                                                                        0 AS juros,
                                                                        0 AS encargos,
                                                                        dividas.data_assinatura,
                                                                        dividas.valor
                                                                    FROM( SELECT 1 
                                                                            FROM (SELECT if(NOT EXISTS(SELECT 1 
                                                                                                        FROM contratos_parcelas cp
                                                                                                        WHERE cp.i_entidades = dividas.i_entidades
                                                                                                            AND cp.i_contratos = dividas.i_contratos), 1, 0) AS par) param 
                                                                        WHERE param.par = 1																																			 		
                                                                    ) AS pex ) AS cp 
                                                        ) 
                            )
                    ) AS js
            FROM(SELECT 								  			  
                        contratos.data_assinatura AS 'data_assinatura',	
                        contratos.i_entidades, 
                        contratos.i_contratos,	
                        contratos_mov_controles.i_exercicios AS 'exercicio',			
                        LEFT(tipos_compromissos.descricao,100), 
                                    
                        (SELECT MAX(reg.id)
                            FROM registro_lotes reg
                        WHERE reg.tipo_registro = 'atos'	
                                AND reg.JSON_store->>'$.content.numero' = CONCAT(LEFT(contratos.i_leis,LENGTH(contratos.i_leis)-2))
                                AND reg.JSON_store->>'$.content.tipo.descricao' = 'LEI') AS 'id_ato',	
                        
                        (SELECT MAX(reg.id)
                            FROM registro_lotes reg
                        WHERE reg.tipo_registro = 'tipos-dividas'	
                                AND reg.JSON_store->>'$.content.descricao' = LEFT(tipos_compromissos.descricao,100)) AS 'tipo',
                                
                        contratos.valor,
                        (SELECT MAX(reg.id)
                        FROM registro_lotes reg
                        WHERE reg.tipo_registro = 'credores'
                                AND reg.refdados->>'$.cpfCnpj' = contratos.cgc_cpf) AS 'credor',
                                    
                        LEFT(contratos.numero_contrato, 16) AS 'numero',
                        LEFT(contratos.especificacao_contrato, 255) AS 'especificacao'
                                                
                FROM contratos,
                    contratos_mov_controles,
                    tipos_compromissos
              WHERE contratos.i_entidades = 1 
                    AND contratos.i_entidades = contratos_mov_controles.i_entidades
                    AND contratos.i_contratos = contratos_mov_controles.i_contratos		
                    AND tipos_compromissos.i_entidades = contratos_mov_controles.i_entidades
                    AND tipos_compromissos.i_tipos_compromissos = contratos_mov_controles.i_tipos_compromissos ) AS dividas
              WHERE dividas.tipo IS NOT NULL """
    return sql
    