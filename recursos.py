# recursos
# executar antes a função:
# BuscaEhSalvaJsonSistemasContabil(token, url, 'recursos', conn)

def recursos_sql (entidade = 1, ano = 2022):
    sql = f""" SELECT 
                        'recursos' AS tipo_registro,
                    MD5(CONCAT(recurso.tipo, recurso.numero, recurso.descricao, recurso.configuracaoRecurso)) as HASH,
                    JSON_OBJECT(
                            'idIntegracao', MD5(CONCAT(recurso.tipo, recurso.numero, recurso.descricao, recurso.configuracaoRecurso)),
                                'content', 				                  
                                JSON_OBJECT(						                       
                                    'configuracaoRecurso', JSON_OBJECT('id', CAST(recurso.configuracaoRecurso AS SIGNED)),
                                    'numero', recurso.numero,
                                            'descricao', recurso.descricao,
                                            'tipo', recurso.tipo
                                )
                        ) AS js 	
                FROM (SELECT 
                        if(recursos.tipo_recurso = 'O', 'ORDINARIO', 'VINCULADO') AS 'tipo',
                        CONCAT('1', lpad(recursos.i_recursos, 3, '0'), '0000') AS 'numero',
                        recursos.descricao AS 'descricao',
                        (SELECT max(reg.json_store->>'$.content.id')
                                FROM registro_lotes reg			  	 		 
                                WHERE reg.tipo_registro = 'configuracoes-recursos'
                                        AND reg.json_store->>'$.content.descricao' = 'Configuração Padrão') AS 'configuracaoRecurso'
                FROM recursos
                WHERE recursos.i_entidades = {entidade} AND 
                NOT EXISTS(SELECT 1 
                            FROM registro_lotes reg	
                            WHERE reg.tipo_registro = 'recursos' AND
                                    reg.id IS NOT NULL AND 
                                    reg.json_store->>'$.content.numero' = CONCAT('1', lpad(recursos.i_recursos, 3, '0'), '0000')) ) recurso  """
    return sql