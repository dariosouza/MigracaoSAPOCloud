# programas

def acoes_sql(ano = 2022):
    sql = f""" SELECT 
		 'acoes' AS tipo_registro,
                 MD5(CONCAT(proj.ppa, proj.numero, proj.descricao)) as HASH,
                 JSON_OBJECT(
                        'idIntegracao', MD5(CONCAT(proj.ppa, proj.numero, proj.descricao)),
                                'content', 				                  
                                JSON_OBJECT(						
                                'ppa', JSON_OBJECT('id', CAST(proj.ppa AS SIGNED)),
                                'numero', proj.numero,
                                                                        'descricao', proj.descricao
                                )
                        ) AS js 	
                        FROM (SELECT   	
                                        (SELECT reg.json_store->>'$.content.id'
                                                FROM registro_lotes reg			  	 		 
                                                WHERE reg.tipo_registro = 'parametros-ppa'  		 
                                                                AND reg.json_store->>'$.content.anoInicial' = ppas.i_exercicios  
                                                                AND reg.json_store->>'$.content.anoFinal' = ppas.exerc_fin) AS 'ppa',
                                        cast(proj_ativ.i_proj_ativ AS CHAR) AS 'numero',
                                        proj_ativ.descricao     
                        FROM proj_ativ,
                                        ppas
                        WHERE proj_ativ.i_exercicios = {ano}
                                        AND proj_ativ.i_ppas = ppas.i_ppas  
                        ORDER BY proj_ativ.i_proj_ativ ) proj
                        WHERE NOT EXISTS(SELECT 1 FROM registro_lotes rg
  					    WHERE rg.tipo_registro = 'acoes'								
						  AND rg.idIntegracao = MD5(CONCAT(proj.ppa, proj.numero, proj.descricao)) )  """
    return sql
    