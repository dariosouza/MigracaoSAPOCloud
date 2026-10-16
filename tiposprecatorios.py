# tipos-precatorios

def tiposprecatorios (entidade = 1, ano = 2022):
    sql = f"""
            SELECT 
                'tipos-precatorios' AS tipo_registro,
                MD5(CONCAT(tipoprec.descricao, tipoprec.tipo, tipoprec.i_tipos_compromissos)) as HASH,	   
                JSON_OBJECT(
                    'idIntegracao', MD5(CONCAT(tipoprec.descricao, tipoprec.tipo, tipoprec.i_tipos_compromissos)),     
                        'content',					 	                  
                            JSON_OBJECT(					 	  
                                'tipo', tipoprec.tipo,
                                'descricao', tipoprec.descricao
                            )
                    ) AS js
            FROM (SELECT tpc.descricao,                 
                            if(tpc.descricao like '%ordinário%', 'ORDINARIO', 'ESPECIAL') as tipo,
                            tpc.i_tipos_compromissos
                    FROM tipos_compromissos tpc join
                            (SELECT i_plano_contas 
                                from parametros 
                            where parametros.ano_exerc = 2022 
                                    and parametros.i_entidades = 1) as param on (tpc.i_plano_contas = param.i_plano_contas)
                    where tpc.i_entidades = 1
                            and tpc.classificacao = 'D'
                            and tpc.descricao LIKE '%Precatórios%' 
            GROUP BY tpc.descricao, tipo, tpc.i_tipos_compromissos ) AS tipoprec	
            WHERE NOT EXISTS(SELECT 1
                                    FROM registro_lotes reg						 	  
                                WHERE reg.tipo_registro = 'tipos-precatorios'
                                        AND (reg.JSON_store->>'$.content.tipo.key' = tipoprec.tipo OR 
                                                reg.JSON_store->>'$.content.tipo' = tipoprec.tipo)
                                        AND reg.JSON_store->>'$.content.descricao' = tipoprec.descricao)  """
    return sql
    