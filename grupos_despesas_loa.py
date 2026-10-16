# grupos-despesas-loa
# BuscaEhSalvaJsonSistemasContabil(token, url, 'grupos-despesas-loa', conn)

def grupos_despesas_loa_sql(entidade = 1, ano = 2022):
    
    sql = f"""
           SELECT 
		'grupos-despesas-loa' AS tipo_registro,
                                MD5(CONCAT(gpdesp.entidade, gpdesp.funcao, gpdesp.programas, gpdesp.organograma, gpdesp.exercicio,
                                                                        gpdesp.acao, gpdesp.subfuncao, gpdesp.loa )) as HASH,
                                JSON_OBJECT(
                                        'idIntegracao', MD5(CONCAT(gpdesp.entidade, gpdesp.funcao, gpdesp.programas, gpdesp.organograma, gpdesp.exercicio,
                                                                                                                        gpdesp.acao,  gpdesp.subfuncao, gpdesp.loa )),
                                        'content', 				                  
                                        JSON_OBJECT(
                                                                        'entidade', JSON_OBJECT('id', CAST(gpdesp.entidade AS SIGNED)),
                                                                                'funcao', JSON_OBJECT('id', CAST(gpdesp.funcao AS SIGNED)),
                                                                                'programa', JSON_OBJECT('id', CAST(gpdesp.programas AS SIGNED)),							
                                                                                        'organograma', JSON_OBJECT('id', CAST(gpdesp.organograma AS SIGNED)),
                                                                                        'exercicio', gpdesp.exercicio,
                                                                                        'acao', JSON_OBJECT('id', CAST(gpdesp.acao AS SIGNED)),							
                                                                                        'subfuncao', JSON_OBJECT('id', CAST(gpdesp.subfuncao AS SIGNED)),
                                                                                        'loa', JSON_OBJECT('id', CAST(gpdesp.loa AS SIGNED)) 
                                                )
                                ) AS js 
                                FROM(SELECT 

                                                300488 AS 'entidade',  /*trocar entidade*/	

                                                (SELECT max(registro_lotes.id)
                                                        FROM registro_lotes, 
                                                                        funcoes 
                                                        WHERE registro_lotes.tipo_registro = 'funcoes' 
                                                                        AND funcoes.i_funcoes = despesas.i_funcoes 
                                                                        AND funcoes.i_atos = 42
                                                                        AND registro_lotes.json_store->>'$.content.numero' = funcoes.i_funcoes  
                                                                        AND registro_lotes.json_store->>'$.content.descricao' = funcoes.descricao) AS 'funcao',
                                                                        
                                        (SELECT max(registro_lotes.id)
                                                        FROM registro_lotes, 
                                                                        programas 
                                                        WHERE registro_lotes.tipo_registro = 'programas' 
                                                                        AND programas.i_entidades = despesas.i_entidades 
                                                                        AND programas.i_programas = despesas.i_programas 
                                                                        AND programas.portaria_func = 42
                                                                        AND registro_lotes.json_store->>'$.content.numero' = programas.i_programas
                                                                        AND registro_lotes.json_store->>'$.content.descricao' = programas.descricao) AS 'programas',
                                                                                                                
                                                (SELECT cast(registro_lotes.id AS SIGNED)
                                        FROM registro_lotes 			  	 		 
                                        WHERE registro_lotes.tipo_registro = 'organogramas' 
                                                AND registro_lotes.json_store->>'$.content.numero' = 
                                                concat(LPAD(despesas.i_orgaos, 2, '0'),LPAD(despesas.i_unidades, 3,'0')) 
                                                AND registro_lotes.json_store->>'$.content.configuracao.id' = 
                                                CAST((SELECT max(reg.json_store->>'$.content.id')
                                                        FROM registro_lotes reg			  	 		 
                                                WHERE reg.tipo_registro = 'configuracoes-organogramas'
                                                        AND reg.json_store->>'$.content.descricao' LIKE '%{ano}%') AS SIGNED))  AS 'organograma',
                                                                                                        
                                                        despesas.ano_exerc AS 'exercicio', 
                                                                        
                                                        (SELECT max(registro_lotes.id)
                                                        FROM registro_lotes, 
                                                                proj_ativ,
                                                                        ppas  
                                                WHERE registro_lotes.tipo_registro = 'acoes' 
                                                                        AND proj_ativ.i_proj_ativ = despesas.i_proj_ativ
                                                                        AND proj_ativ.i_exercicios = despesas.ano_exerc
                                                                        AND proj_ativ.i_ppas = ppas.i_ppas 
                                                                        AND {ano} BETWEEN ppas.i_exercicios AND ppas.exerc_fin 
                                                                        AND registro_lotes.json_store->>'$.content.numero' = proj_ativ.i_acoes
                                                                        AND registro_lotes.json_store->>'$.content.descricao' = proj_ativ.descricao) AS 'acao',
                                                                                                                                
                                                        #SELECT * FROM despesas
                                                        (SELECT max(registro_lotes.id)
                                                        FROM registro_lotes, 
                                                                subfuncoes  
                                                WHERE registro_lotes.tipo_registro = 'subfuncoes' 
                                                                        AND subfuncoes.i_subfuncoes = despesas.i_subs
                                                                        AND subfuncoes.i_atos = 42
                                                                        AND registro_lotes.json_store->>'$.content.numero' = subfuncoes.i_subfuncoes
                                                                        AND registro_lotes.json_store->>'$.content.descricao' = subfuncoes.descricao) AS 'subfuncao',
                                                        
                                                        (SELECT max(registro_lotes.id)
                                                        FROM registro_lotes			   	  
                                                WHERE registro_lotes.tipo_registro = 'parametros-loa'			 		    
                                                                        AND registro_lotes.json_store->>'$.content.exercicio' = {ano}) AS 'loa'
                                                                                                
                                FROM despesas,
                                                ppas  		 
                                WHERE despesas.i_entidades = {entidade}
                                                AND despesas.ano_exerc = {ano}  
                                                and despesas.valor <> 0
                                                AND despesas.portaria_func = 42
                                                and despesas.ano_exerc between ppas.i_exercicios and ppas.exerc_fin  
                                and ppas.dt_aprovacao is not null ) AS gpdesp 
                                WHERE NOT EXISTS(SELECT * 
                                                FROM registro_lotes 
                                                WHERE registro_lotes.tipo_registro = 'grupos-despesas-loa'
                                                                and registro_lotes.json_store->>'$.content.loa.id' = gpdesp.loa
                                                                and registro_lotes.json_store->>'$.content.acao.id' = gpdesp.acao
                                                                and registro_lotes.json_store->>'$.content.funcao.id' = gpdesp.funcao
                                                                and registro_lotes.json_store->>'$.content.entidade.id' = gpdesp.entidade
                                                                and registro_lotes.json_store->>'$.content.programa.id' = gpdesp.programas
                                                                and registro_lotes.json_store->>'$.content.subfuncao.id' = gpdesp.subfuncao
                                                                and registro_lotes.json_store->>'$.content.organograma.id' = gpdesp.organograma) 
                                GROUP BY gpdesp.loa, gpdesp.acao, gpdesp.funcao, gpdesp.entidade, gpdesp.programas, gpdesp.subfuncao, gpdesp.organograma,
                                                        gpdesp.exercicio
                                """
    return sql
                