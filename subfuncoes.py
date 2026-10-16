# subfuncoes
# BuscaEhSalvaJsonSistemasContabil(token, url, 'subfuncoes', conn)

def subfuncoes_sql (entidade = 1, ano = 2022):
    sql = f""" 
                SELECT 
                    'subfuncoes' AS tipo_registro,
                        MD5(CONCAT(subf.numero, subf.descricao, subf.configuracao)) as HASH,
                        JSON_OBJECT(
                                'idIntegracao', MD5(CONCAT(subf.numero, subf.descricao, subf.configuracao)),
                                    'content', 				                  
                                    JSON_OBJECT(                       
                                                'descricao', subf.descricao,
                                                'numero', subf.numero,
                                                'configuracao', JSON_OBJECT('id', CAST(subf.configuracao AS SIGNED))
                                    )
                            ) AS js 
                    FROM (SELECT 
                            subfuncoes.i_subFuncoes AS 'numero',
                            subfuncoes.descricao AS 'descricao',
                            (SELECT max(reg.id)
                                FROM registro_lotes reg
                                WHERE reg.tipo_registro = 'configuracoes-funcionais' AND 
                                        reg.json_store->>'$.content.descricao' = 'MOG - PORTARIA Nº 42/99') AS 'configuracao'
                    FROM subfuncoes ) AS subf
                    WHERE NOT EXISTS(SELECT 1
                                            FROM registro_lotes reg 
                                            WHERE reg.tipo_registro = 'subfuncoes' 
                                                    AND reg.json_store->>'$.content.numero' = subf.numero 
                                                    AND reg.json_store->>'$.content.configuracao.id' = subf.configuracao) 
                        """
    return sql