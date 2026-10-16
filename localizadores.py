# localizadores

def localizadores_sql (entidade = 1, ano = 2022):
    sql = f"""
                SELECT 
                        'localizadores' AS tipo_registro,
                    MD5(CONCAT(lc.descricao, lc.ppa)) as HASH,
                    JSON_OBJECT(
                            'idIntegracao', MD5(CONCAT(lc.descricao, lc.ppa)),
                                'content', 				                  
                                JSON_OBJECT(                       
                                            'descricao', lc.descricao,
                                            'ppa', JSON_OBJECT('id', CAST(lc.ppa AS SIGNED))
                                )
                        ) AS js 
                FROM ( SELECT 
                                localizadores.descricao AS 'descricao',
                                (SELECT reg.json_store->>'$.content.id'
                                        FROM registro_lotes reg			  	 		 
                                        WHERE reg.tipo_registro = 'parametros-ppa'  		 
                                                AND 2022 between reg.json_store->>'$.content.anoInicial' AND 
                                                                        reg.json_store->>'$.content.anoFinal') AS 'ppa'
                        from localizadores ) AS lc """
    return sql