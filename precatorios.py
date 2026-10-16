# precatorios

def precatorios (entidade = 1, ano = 2022):
    sql = f"""
                SELECT 
                'precatorios' AS tipo_registro,
                MD5(CONCAT(precatorios.i_entidades, precatorios.i_contratos, precatorios.exercicio)) as HASH,	  
                JSON_OBJECT(
                'idIntegracao', MD5(CONCAT(precatorios.i_entidades, precatorios.i_contratos, precatorios.exercicio)),     
                    'content',					 	                  
                        JSON_OBJECT(					 	  							                 
                            'ato', JSON_OBJECT('id', CAST(precatorios.id_ato AS SIGNED)),
                            'data', precatorios.data_assinatura,
                            'tipo', JSON_OBJECT('id', CAST(precatorios.tipo AS SIGNED)),
                            'valor', precatorios.valor,
                                'credor', JSON_OBJECT('id', CAST(precatorios.credor AS SIGNED)),
                                'numero', precatorios.numero,
                                'exercicio', CAST(precatorios.exercicio AS SIGNED),
                                'especificacao', precatorios.especificacao,
                                'parcelas', (SELECT JSON_ARRAYAGG(JSON_OBJECT('numero', cp.numero_parcela,						  													
                                                                              'dataVencimento', cp.data_vencimento,
                                                                              'valor', cp.valor))
                                                    FROM(SELECT cp.numero_parcela,													 		  
                                                                    cp.data_vencimento,
                                                                    cp.valor  
                                                            FROM contratos_parcelas cp
                                                            WHERE cp.i_entidades = precatorios.i_entidades
                                                                    AND cp.i_contratos = precatorios.i_contratos
                                                        UNION ALL 
                                                            SELECT 1 AS numero_parcela, 												    		   
                                                                    precatorios.data_assinatura,
                                                                    precatorios.valor
                                                                FROM( SELECT 1 
                                                                        FROM (SELECT if(NOT EXISTS(SELECT 1 
                                                                                                    FROM contratos_parcelas cp
                                                                                                    WHERE cp.i_entidades = precatorios.i_entidades
                                                                                                          AND cp.i_contratos = precatorios.i_contratos), 1, 0) AS par) param 
                                                                        WHERE param.par = 1																																			 		
                                                                ) AS pex ) AS cp 
                                                    ) 
                        )
                ) AS js
        FROM(SELECT 								  			  
                    contratos.data_assinatura AS 'data_assinatura',	
                    precatorios.data_apresentacao AS 'dataApresentacao',
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
                    WHERE reg.tipo_registro = 'tipos-precatorios'	
                            AND reg.JSON_store->>'$.content.descricao' = LEFT(tipos_compromissos.descricao,100)) AS 'tipo',
                            
                    contratos.valor,
                    (SELECT MAX(reg.id)
                    FROM registro_lotes reg
                    WHERE reg.tipo_registro = 'credores'
                            AND reg.refdados->>'$.cpfCnpj' = contratos.cgc_cpf) AS 'credor',
                                
                    LEFT(precatorios.numero_precatorio, 16) AS 'numero',
                    LEFT(precatorios.historico, 255) AS 'especificacao'
                                            
            FROM contratos,
                contratos_mov_controles,
                tipos_compromissos,
                precatorios 
            WHERE contratos.i_entidades = {entidade} 
                AND contratos.i_entidades = contratos_mov_controles.i_entidades
                    AND contratos.i_contratos = contratos_mov_controles.i_contratos		
                    AND tipos_compromissos.i_entidades = contratos_mov_controles.i_entidades
                AND tipos_compromissos.i_tipos_compromissos = contratos_mov_controles.i_tipos_compromissos
                    AND contratos.i_entidades = precatorios.i_entidades 
                    AND contratos.i_precatorios = precatorios.i_precatorios  ) AS precatorios
    """
    return sql
    