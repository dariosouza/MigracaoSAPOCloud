# programas

def programas_sql(entidade = 1, ano = 2022):
    sql = f""" SELECT 
                    'programas' AS tipo_registro,
                MD5(CONCAT(prog.ppa, prog.numero, prog.objetivos, prog.horizonteTemporal, prog.descricao)) as HASH,
                JSON_OBJECT(
                        'idIntegracao', MD5(CONCAT(prog.ppa, prog.numero, prog.objetivos, prog.horizonteTemporal, prog.descricao)),
                            'content', 				                  
                            JSON_OBJECT(						
                                'ppa', JSON_OBJECT('id', CAST(prog.ppa AS SIGNED) ),
                                'numero', prog.numero,
                                        'objetivos', prog.objetivos,
                                        'horizonteTemporal', prog.horizonteTemporal,
                                        'descricao', prog.descricao
                            )
                    ) AS js 	
            FROM ( SELECT 
                        (SELECT reg.json_store->>'$.content.id'
                            FROM registro_lotes reg
                            WHERE reg.tipo_registro = 'parametros-ppa'  		 
                                    AND reg.json_store->>'$.content.anoInicial' = ppas.i_exercicios  
                                    AND reg.json_store->>'$.content.anoFinal' = ppas.exerc_fin) AS 'ppa',
                            programas.i_programas AS numero,
                            programas.objetivo AS objetivos,
                            (SELECT if(max(hspr.horiz_temporal) = 'C', 'CONTINUO', 'TEMPORARIO') 
                                FROM hist_programas hspr
                            WHERE hspr.i_ppas = ppas.i_ppas 
                                    AND hspr.i_programas = programas.i_programas 
                                    AND hspr.i_entidades = programas.i_entidades) AS 'horizonteTemporal',
                            programas.descricao AS 'descricao'  
                    FROM programas,
                            ppas
                    WHERE programas.i_entidades = {entidade} 
                            AND programas.ano_exerc = {ano}
                            AND programas.ano_exerc BETWEEN ppas.i_exercicios AND ppas.exerc_fin
                    ORDER BY i_programas ) prog 
                    WHERE NOT EXISTS(SELECT 1 FROM registro_lotes rg
  					    WHERE rg.tipo_registro = 'programas' 
                              AND rg.status != 'SUCESSO' 
						  	  AND rg.idIntegracao = MD5(CONCAT(prog.ppa, prog.numero, prog.objetivos, prog.horizonteTemporal, prog.descricao)) ) """
    return sql
    