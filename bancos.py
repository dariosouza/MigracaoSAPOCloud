# bancos
# deve-se apenas buscar os dados dos bancos
# Todos os bancos já estão cadastrados 
# BuscaEhSalvaJsonSistemasContabil(token, url, 'bancos', conn)

def bancos (entidade = 1, ano = 2022):
    sql = f"""
                SELECT 
                'agencias-bancarias' AS tipo_registro,
                 MD5(CONCAT(ag.id_banco, ag.agencia, coalesce(ag.dv,''))) as HASH,	   
                 JSON_OBJECT(
                        'idIntegracao', MD5(CONCAT(ag.id_banco, ag.agencia, coalesce(ag.dv,''))),     
                            'content',
                                JSON_MERGE_PRESERVE(
                                JSON_OBJECT(
                                        'nome', ag.nome,
                                        'numero', cast(ag.agencia AS CHAR),							
                                    'banco', JSON_OBJECT('id', CAST(ag.id_banco AS SIGNED))
                                ),
                                if(ag.dv IS NOT NULL, JSON_OBJECT('digito', ag.dv), JSON_OBJECT())
                            )
                    ) AS js 
                FROM(SELECT 
                        (SELECT reg.id
                            FROM registro_lotes reg
                        WHERE reg.tipo_registro = 'bancos' 
                                AND reg.JSON_store->>'$.content.numero' = 
                                        LPAD(agencias.i_bancos,3, '0')) AS 'id_banco',
                        agencias.i_agencias AS 'agencia', 			 	
                        agencias.nome AS 'nome',
                        agencias.dv_agencia AS 'dv' 				
                FROM agencias ) ag 
            WHERE NOT EXISTS(SELECT 1
                               FROM registro_lotes reg
                               WHERE reg.tipo_registro = 'agencias-bancarias'
                                     AND reg.JSON_store->>'$.content.banco.id' = ag.id_banco
                                     AND reg.JSON_store->>'$.content.numero' = ag.agencia
                                     AND reg.JSON_store->>'$.content.digito' = ag.dv)
        """
    return sql
        
