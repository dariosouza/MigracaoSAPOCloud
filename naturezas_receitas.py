# 'naturezas-receitas'
# rodar antes: BuscaEhSalvaJsonSistemasContabil(token, url, 'configuracoes-naturezas-receitas', conn)

def naturezas_receitas_sql(entidade = 1, ano = 2022):
    sql = f""" 
             SELECT 
                    'naturezas-receitas' AS tipo_registro,
                        MD5(CONCAT(rubr.numero, rubr.descricao, rubr.tipo, rubr.configuracao)) as HASH,
                        JSON_OBJECT(
                                'idIntegracao', MD5(CONCAT(rubr.numero, rubr.descricao, rubr.tipo, rubr.configuracao)),
                                'content', 				                  
                                JSON_OBJECT('configuracao', JSON_OBJECT('id', CAST(rubr.configuracao AS SIGNED)),
                                            'numero', rubr.numero,
                                            'descricao', rubr.descricao,
                                            'tipo', rubr.tipo
                                )
                        ) AS js 	
                FROM (SELECT 		 
                        LEFT(if(substr(i_rubricas,1,1) = '4', substr(rubricas.i_rubricas,2, length(rubricas.i_rubricas)-1), rubricas.i_rubricas), 14) AS 'numero',
                         left(rubricas.descricao, 150) AS 'descricao',
                        if(rubricas.tipo_rubrica = 'A', 'ANALITICO', 'SINTETICO') AS 'tipo',
                        (SELECT max(reg.json_store->>'$.content.id')
                                FROM registro_lotes reg
                                WHERE reg.tipo_registro = 'configuracoes-naturezas-receitas'
                                        AND reg.json_store->>'$.content.descricao' = 'Portaria da Receita - {ano}') AS 'configuracao'
                        FROM rubricas
                        WHERE rubricas.i_entidades = {entidade} 
                                /*AND (rubricas.portaria_rubr = {ano} OR rubricas.portaria_anterior = {ano}) */
                                and rubricas.i_rubricas not like '9%' 
                                and rubricas.i_rubricas not like '49%' 
                                and left(rubricas.i_rubricas, 14) <> '00000000000000'
                        ORDER BY tipo DESC ) AS rubr
                WHERE NOT EXISTS(SELECT *
                                FROM registro_lotes reg	
                                WHERE reg.tipo_registro = 'naturezas-receitas' AND
                                        reg.id IS NOT NULL 
                                        AND reg.json_store->>'$.content.numero' = rubr.numero  
                                        AND reg.json_store->>'$.content.configuracao.id' = rubr.configuracao) """
    return sql 