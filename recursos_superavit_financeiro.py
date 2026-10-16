# recursos do superavit começando com 2 (instrução Rômulo...)

def recursos_superavit_financeiro(entidade = 1, ano = 2022):
    sql = f""" SELECT 
                    'recursos' AS tipo_registro,
                    MD5(CONCAT(desp.tipo, desp.descricao, desp.numero, desp.configuracaoRecurso)) as HASH,
                    JSON_OBJECT(
                        'idIntegracao', MD5(CONCAT(desp.tipo, desp.descricao, desp.numero, desp.configuracaoRecurso)),
                        'content', 				                  
                        JSON_OBJECT('tipo', desp.tipo,
                                        'configuracaoRecurso', JSON_OBJECT('id', cast(desp.configuracaoRecurso AS signed)),
                                        'numero', desp.numero,
                                        'descricao', desp.descricao
                        )
                    ) AS js    
            FROM (SELECT 
                        if(recursos.tipo_recurso = 'O', 'ORDINARIO', 'VINCULADO') AS 'tipo',
                        left(recursos.descricao, 150) AS 'descricao',
                        CONCAT('2', LPAD(recursos.i_recursos, 3, '0'), '0000') AS 'numero', /*2 na frente usado para Superávit*/
                        (SELECT max(reg.json_store->>'$.content.id')
                            FROM registro_lotes reg
                        WHERE reg.tipo_registro = 'configuracoes-recursos'
                                AND reg.json_store->>'$.content.descricao' = 'Configuração Padrão') AS 'configuracaoRecurso'
                FROM recursos 
                WHERE recursos.i_entidades = {entidade}
                        AND recursos.i_recursos IN (SELECT DISTINCT i_recursos
                                                            FROM movto_supl
                                                            WHERE movto_supl.i_entidades = recursos.i_entidades 
                                                                    AND movto_supl.ano_exerc = {ano}
                                                                    AND movto_supl.origem_recurso = 2  /*Superávit financeiro*/ )
                        AND NOT EXISTS(SELECT 1
                                         FROM registro_lotes 
                                        WHERE registro_lotes.tipo_registro = 'recursos'
                                              AND registro_lotes.id IS NOT NULL	 
                                              AND registro_lotes.json_store->>'$.content.numero' = CONCAT('2', LPAD(recursos.i_recursos, 3, '0'), '0000')			
                                              AND registro_lotes.json_store->>'$.content.descricao' = left(recursos.descricao, 150)
                                              AND registro_lotes.json_store->>'$.content.configuracaoRecurso.id' = 
                                              (SELECT max(reg.json_store->>'$.content.id')
                                                 FROM registro_lotes reg			  	 		 
                                                WHERE reg.tipo_registro = 'configuracoes-recursos'
                                                      AND reg.json_store->>'$.content.descricao' = 'Configuração Padrão'))) AS desp
                """
    return sql