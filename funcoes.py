# funcoes

def funcoes_sql (entidade = 1, ano = 2022):
    sql = f"""
                SELECT 
                    'funcoes' AS tipo_registro,
                MD5(CONCAT(funcao.numero, funcao.descricao, funcao.configuracao)) as HASH,
                JSON_OBJECT(
                        'idIntegracao', MD5(CONCAT(funcao.numero, funcao.descricao, funcao.configuracao)),
                            'content', 				                  
                            JSON_OBJECT(                       
                                        'descricao', funcao.descricao,
                                        'numero', funcao.numero,
                                        'configuracao', JSON_OBJECT('id', CAST(funcao.configuracao AS SIGNED))
                            )
                    ) AS js 
            FROM (SELECT 
                    funcoes.i_funcoes AS 'numero',
                    funcoes.descricao AS 'descricao',
                    (SELECT max(reg.id)
                        FROM registro_lotes reg
                        WHERE reg.tipo_registro = 'configuracoes-funcionais' AND 
                                reg.json_store->>'$.content.descricao' = 'MOG - PORTARIA Nº 42/99') AS 'configuracao'
            FROM funcoes ) AS funcao
            WHERE NOT EXISTS(SELECT 1
                                    FROM registro_lotes reg 
                                    WHERE reg.tipo_registro = 'funcoes' 
                                            AND reg.json_store->>'$.content.numero' = funcao.numero 
                                            AND reg.json_store->>'$.content.configuracao.id' = funcao.configuracao)  
            """
    return sql
    