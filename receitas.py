# receitas
# "https://pla-sl-rest.betha.cloud/planejamento/service-layer/v2/api/"
# BuscaEhSalvaJsonSistemasContabil(token, url, 'receitas-loa', conn)    

def receitas_sql (entidade = 1, ano = 2022):
    sql = f"""
            SELECT 
         'receitas-loa' AS tipo_registro,                   			     
          MD5(CONCAT(receitas.entidade, receitas.metaFinanceira, receitas.numero,
                          receitas.i_rubricas, receitas.natureza, receitas.recurso,
                          receitas.percentual, receitas.valor, receitas.organograma,
                          receitas.exercicio, receitas.loa, receitas.i_rubricas)) as HASH,   
          JSON_OBJECT(
                  'idIntegracao', MD5(CONCAT(receitas.entidade, receitas.metaFinanceira, receitas.numero,
                          receitas.i_rubricas, receitas.natureza, receitas.recurso,
                          receitas.percentual, receitas.valor, receitas.organograma,
                          receitas.exercicio, receitas.loa, receitas.i_rubricas)),
                      'content', 
							 
							 JSON_MERGE_PRESERVE(		
							 		                  
	                      JSON_OBJECT(						                       
	                          'entidade', JSON_OBJECT('id', CAST(receitas.entidade AS SIGNED)),
	                          'metaFinanceira', receitas.valor,
	                          'numero', receitas.numero,
	                          'natureza', JSON_OBJECT('id', CAST(receitas.natureza AS SIGNED)),								  	                         								  	                         
									  	                         
	                          'recursos', JSON_ARRAY( JSON_OBJECT('recurso', JSON_OBJECT('id', CAST(receitas.recurso AS SIGNED)),
		                                                           'percentual', receitas.percentual,
		                                                           'valor', receitas.valor ) ),
		                                                         
		                       'organograma', JSON_OBJECT('id', CAST(receitas.organograma AS SIGNED)),
		                       'exercicio', receitas.exercicio,
		                       'loa', JSON_OBJECT('id', CAST(receitas.loa AS SIGNED))		                       		                       
	                      ),
								 if(receitas.valor_deducoes IS NOT NULL,
								 	 JSON_OBJECT('deducoes', JSON_ARRAY( JSON_OBJECT('deducao',
									  												JSON_OBJECT('id', CAST(receitas.deducao AS SIGNED)),
																					  			   'valor', receitas.valor_deducoes,
																									'percentual', ROUND( (receitas.valor_deducoes / receitas.valor) * 100, 2),
																									'recursos', JSON_ARRAY( JSON_OBJECT( 'recurso', JSON_OBJECT('id', CAST(receitas.recurso AS SIGNED)), 'percentual', 100, 'valor', receitas.valor_deducoes ) )) ) ),
									 JSON_OBJECT() )
                      )
                      
              ) AS js

      FROM (

      SELECT 
              300488 AS 'entidade',  /*trocar entidade*/
              receitas.valor AS 'metaFinanceira',
              receitas.i_receitas AS 'numero',		 		 		 
              receitas.i_rubricas,		 
              
              (SELECT max(reg.json_store->>'$.content.id')
                  FROM registro_lotes reg			  	 		 
                  WHERE reg.tipo_registro = 'naturezas-receitas'
                          AND reg.json_store->>'$.content.numero' = LEFT(if(substr(i_rubricas,1,1) = '4', substr(receitas.i_rubricas,2, length(receitas.i_rubricas)-1), receitas.i_rubricas), 14)  
                          AND reg.json_store->>'$.content.configuracao.id' = 
                          (SELECT cast(max(reg.id) AS SIGNED)
                          FROM registro_lotes reg			  	 		 
                          WHERE reg.tipo_registro = 'configuracoes-naturezas-receitas'
                                  AND reg.json_store->>'$.content.descricao' = 'Portaria da Receita - {ano}')) AS 'natureza',
                                  
              /*-----------------------------------------*/			
              (SELECT max(reg.id)
                  FROM registro_lotes reg			  	 		 
                  WHERE reg.tipo_registro = 'recursos' 
                          AND reg.JSON_store->>'$.content.numero' = CONCAT('1', lpad(receitas.i_recursos, 3, '0'), '0000')
                          AND reg.JSON_store->>'$.content.configuracaoRecurso.id' =
                              (SELECT max(reg.json_store->>'$.content.id')
                                  FROM registro_lotes reg			  	 		 
                                  WHERE reg.tipo_registro = 'configuracoes-recursos'
                                      AND reg.json_store->>'$.content.descricao' = 'Configuração Padrão')) AS 'recurso',
              
              100 AS 'percentual',
              receitas.valor AS 'valor',
                                                  
              (SELECT cast(reg.id AS SIGNED)
                  FROM registro_lotes reg			  	 		 
                  WHERE reg.tipo_registro = 'organogramas' 
                      AND reg.json_store->>'$.content.numero' = 
                          concat(LPAD(receitas.i_orgaos, 2, '0'),LPAD(receitas.i_unidades, 3,'0')) 
                          AND reg.json_store->>'$.content.configuracao.id' = 
                          CAST((SELECT max(reg.json_store->>'$.content.id')
                              FROM registro_lotes reg
                                  WHERE reg.tipo_registro = 'configuracoes-organogramas'
                                          AND reg.json_store->>'$.content.descricao' LIKE '%{ano}%') AS SIGNED) )  AS 'organograma',
              
              receitas.ano_exerc AS 'exercicio',
              
              (SELECT reg.id
                  FROM registro_lotes reg	
                  WHERE reg.tipo_registro = 'parametros-loa'
                          AND reg.JSON_store->>'$.content.exercicio' = receitas.ano_exerc) AS 'loa',					
					
					(SELECT rec.valor
						FROM receitas rec 
					  WHERE right(rec.i_rubricas, 14) = right(receitas.i_rubricas, 14) and
					  		  rec.i_recursos = receitas.i_recursos AND 
					  		  rec.ano_exerc = receitas.ano_exerc AND 
					  		  rec.i_entidades = receitas.i_entidades AND 
							  /*rec.i_receitas != receitas.i_receitas*/
							  rec.i_rubricas LIKE '9%'
							) AS 'valor_deducoes',
							
					#SELECT * FROM tipo_deducao
					(SELECT max(reg.id)
                  FROM registro_lotes reg	
                  WHERE reg.tipo_registro = 'deducoes-receitas'
                  		AND reg.id IS NOT NULL 
                        AND reg.JSON_store->>'$.content.tipo' = 					
							   (SELECT 
							 			case max(tded.tipo_stn)
										   when 1 then 'RENUNCIA'
										   when 2 then 'RESTITUICOES'
										   when 3 then 'DESCONTOS_CONCEDIDOS'
										   when 5 then 'FUNDEB'
										   when 6 then 'COMPENSACOES'
										   when 8 then 'RETIFICACOES'
										   when 9 then 'OUTRAS_DEDUCOES'
										   else 'OUTRAS_DEDUCOES'
										END AS 'tipo'
								FROM receitas rec,
									  tipo_deducao tded	 
							  WHERE right(rec.i_rubricas, 14) = right(receitas.i_rubricas, 14) and
							  		  rec.i_recursos = receitas.i_recursos AND 
							  		  rec.ano_exerc = receitas.ano_exerc AND 
							  		  rec.i_entidades = receitas.i_entidades AND 
									  rec.i_tipo_deducao = tded.i_tipo_deducao AND 
									  rec.i_entidades = tded.i_entidades AND 
									  rec.i_rubricas LIKE '9%'
									) ) AS 'deducao'
									
      from receitas 
     where receitas.ano_exerc = {ano} 
           and receitas.i_entidades = {entidade} ) AS receitas  		 
    WHERE receitas.valor > 0 AND 
		  	 receitas.natureza IS NOT NULL """
    return sql