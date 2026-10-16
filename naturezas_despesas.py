# naturezas-receitas

def naturezas_despesas_sql (entidade = 1, ano = 2022):

    sql = f"""SELECT 
                    'naturezas-despesas' AS tipo_registro,
                MD5(CONCAT(elem_desp.tipo, elem_desp.numero, elem_desp.descricao, elem_desp.configuracao)) as HASH,
                JSON_OBJECT(
                        'idIntegracao', MD5(CONCAT(elem_desp.tipo, elem_desp.numero, elem_desp.descricao, elem_desp.configuracao)),
                            'content', 				                  
                            JSON_OBJECT(						                       
                                'configuracao', JSON_OBJECT('id', CAST(elem_desp.configuracao AS SIGNED)),
                                'numero', elem_desp.numero,
                                        'descricao', elem_desp.descricao,
                                        'tipo', elem_desp.tipo
                            )
                    ) AS js 	
            FROM (SELECT 
                        if(elementos.tipo_elemento = 'A', 'ANALITICO', 'SINTETICO') AS 'tipo',
                        elementos.i_elementos AS 'numero',
                        elementos.descricao AS 'descricao',
                        (SELECT max(reg.json_store->>'$.content.id')
                            FROM registro_lotes reg			  	 		 
                            WHERE reg.tipo_registro = 'configuracoes-naturezas-despesas'
                                    AND reg.json_store->>'$.content.descricao' LIKE '%{ano}%') AS 'configuracao'
                FROM elementos 
                WHERE elementos.portaria = {ano} 
                        AND elementos.i_entidades = {entidade}
                ORDER BY tipo DESC ) elem_desp
            WHERE not EXISTS(SELECT 1 FROM registro_lotes reg
                                WHERE tipo_registro = 'naturezas-despesas'
                                      AND reg.idIntegracao = MD5(CONCAT(elem_desp.tipo, elem_desp.numero, elem_desp.descricao, elem_desp.configuracao)) 
                                      AND reg.id IS not NULL)  """
    return sql