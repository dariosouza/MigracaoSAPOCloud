# 'despesas-loa'

def despesas_loa_sql(entidade = 1, ano = 2022):
    sql = f""" 
                SELECT 
		'despesas-loa' AS tipo_registro,
                        MD5(CONCAT(desp.loa, desp.organograma, desp.natureza, desp.programas, desp.funcao, desp.acao, 
                                                                desp.subfuncao, desp.metaFinanceira, desp.ano_exerc, desp.numero, desp.ListDespesas)) as HASH,
                        JSON_OBJECT(
                                'idIntegracao', MD5(CONCAT(desp.loa, desp.organograma, desp.natureza, desp.programas, desp.funcao, desp.acao, 
                                                                                                                desp.subfuncao, desp.metaFinanceira, desp.ano_exerc, desp.numero, desp.ListDespesas)),
                                'content', 				                  
                                JSON_OBJECT(
                                        'loa', JSON_OBJECT('id', CAST(desp.loa AS SIGNED)),  															         				
                                        'natureza',JSON_OBJECT('id', CAST(desp.natureza AS SIGNED)),      
                                                        'metaFinanceira', desp.metaFinanceira,
                                                        'exercicio', desp.ano_exerc,
                                                        'numero', desp.numero,
                                                        
                                                        'grupo', JSON_OBJECT('id', (SELECT cast(max(reg.id) AS SIGNED)
                                                                                        FROM registro_lotes reg			  	 		 
                                                                                        WHERE reg.tipo_registro = 'grupos-despesas-loa'
                                                                                                        AND reg.JSON_store->>'$.content.organograma.id' = desp.organograma
                                                                                                        AND reg.JSON_store->>'$.content.funcao.id' = desp.funcao										  		  
                                                                                                        AND reg.JSON_store->>'$.content.subfuncao.id' = desp.subfuncao
                                                                                                        AND reg.JSON_store->>'$.content.programa.id' = desp.programas
                                                                                                        AND reg.JSON_store->>'$.content.acao.id' = desp.acao
                                                                                                        AND reg.JSON_store->>'$.content.loa.id' = desp.loa) ),
                                                                                                                
                                                        'recursos', (SELECT 
                                                                        JSON_ARRAYAGG( JSON_OBJECT('recurso',
                                                                        JSON_OBJECT('id', (SELECT cast(max(reg.id) AS SIGNED)
                                                                                                                        FROM registro_lotes reg			  	 		 
                                                                                                                        WHERE reg.tipo_registro = 'recursos' 
                                                                                                                                AND reg.JSON_store->>'$.content.numero' = CONCAT('1', lpad(despc.dprecur, 3, '0'), '0000')
                                                                                                                                AND reg.JSON_store->>'$.content.configuracaoRecurso.id' =
                                                                                                                                (SELECT max(reg.json_store->>'$.content.id')
                                                                                                                                FROM registro_lotes reg			  	 		 
                                                                                                                                WHERE reg.tipo_registro = 'configuracoes-recursos'
                                                                                                                                        AND reg.json_store->>'$.content.descricao' = 'Configuração Padrão')) ), 
                                                                        'percentual', ROUND(((despc.vlrcalc * 100) / desp.metaFinanceira),2),
                                                                        'valor', despc.vlrcalc ))
                                                        FROM(SELECT 
                                                                        despesas.i_recursos AS dprecur,
                                                                        sum(despesas.valor) AS vlrcalc
                                                        FROM despesas 
                                                        WHERE despesas.i_entidades =  desp.i_entidades
                                                                AND despesas.ano_exerc =  desp.ano_exerc 
                                                                AND FIND_IN_SET(despesas.i_despesas, desp.ListDespesas)
                                                        GROUP BY despesas.i_recursos) AS despc) 
                                                )
                        ) AS js 
                        FROM (SELECT  
                                                        
                                                (SELECT max(registro_lotes.id)
                                                FROM registro_lotes			   	  
                                        WHERE registro_lotes.tipo_registro = 'parametros-loa'			 		    
                                                                AND registro_lotes.json_store->>'$.content.exercicio' = {ano}) AS 'loa',

                                                (SELECT cast(registro_lotes.id AS SIGNED)
                                        FROM registro_lotes 			  	 		 
                                        WHERE registro_lotes.tipo_registro = 'organogramas' 
                                        AND registro_lotes.json_store->>'$.content.numero' = 
                                        concat(LPAD(despesas.i_orgaos, 2, '0'),LPAD(despesas.i_unidades, 3,'0')) 
                                        AND registro_lotes.json_store->>'$.content.configuracao.id' = 
                                        CAST((SELECT max(reg.json_store->>'$.content.id')
                                                FROM registro_lotes reg			  	 		 
                                                WHERE reg.tipo_registro = 'configuracoes-organogramas'
                                                        AND reg.json_store->>'$.content.descricao' LIKE '%{ano}%') AS SIGNED)) AS 'organograma',
                                                
                                (SELECT max(registro_lotes.id)
                                                        FROM registro_lotes, 
                                                                elementos 
                                                WHERE registro_lotes.tipo_registro = 'naturezas-despesas' 
                                                                        AND elementos.i_entidades = despesas.i_entidades
                                                                        AND elementos.i_elementos = despesas.i_elementos
                                                                        AND elementos.portaria = despesas.ano_exerc
                                                                        AND registro_lotes.json_store->>'$.content.numero' = elementos.i_elementos) AS 'natureza', 
                                
                                (SELECT max(registro_lotes.id)
                                                        FROM registro_lotes, 
                                                                        programas 
                                                        WHERE registro_lotes.tipo_registro = 'programas' 
                                                                        AND programas.i_entidades = despesas.i_entidades 
                                                                        AND programas.i_programas = despesas.i_programas 
                                                                        AND programas.portaria_func = 42
                                                                        AND registro_lotes.json_store->>'$.content.numero' = programas.i_programas
                                                                        AND registro_lotes.json_store->>'$.content.descricao' = programas.descricao) AS 'programas',      
                                                                        
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
                                                                proj_ativ,
                                                                        ppas pa  
                                                WHERE registro_lotes.tipo_registro = 'acoes' 
                                                                        AND proj_ativ.i_proj_ativ = despesas.i_proj_ativ
                                                                        AND proj_ativ.i_exercicios = despesas.ano_exerc
                                                                        AND proj_ativ.i_ppas = pa.i_ppas 
                                                                        AND {ano} BETWEEN pa.i_exercicios AND pa.exerc_fin 
                                                                        AND registro_lotes.json_store->>'$.content.numero' = proj_ativ.i_acoes
                                                                        AND registro_lotes.json_store->>'$.content.descricao' = proj_ativ.descricao) AS 'acao',		
                                
                                (SELECT max(registro_lotes.id)
                                                        FROM registro_lotes, 
                                                                subfuncoes  
                                                WHERE registro_lotes.tipo_registro = 'subfuncoes' 
                                                                        AND subfuncoes.i_subfuncoes = despesas.i_subs
                                                                        AND subfuncoes.i_atos = 42
                                                                        AND registro_lotes.json_store->>'$.content.numero' = subfuncoes.i_subfuncoes
                                                                        AND registro_lotes.json_store->>'$.content.descricao' = subfuncoes.descricao) AS 'subfuncao',
                                                                                                                
                                sum(despesas.valor) AS 'metaFinanceira',
                                despesas.ano_exerc,
                                despesas.i_entidades,
                                min(despesas.i_despesas) AS 'numero',
                                GROUP_CONCAT(despesas.i_despesas) AS 'ListDespesas'
                                
                                FROM despesas join
                                elementos on (despesas.i_entidades = elementos.i_entidades and despesas.portaria = elementos.portaria and
                                                despesas.i_elementos = elementos.i_elementos) 
                                                join localizadores on (despesas.i_localizadores = localizadores.i_localizadores),
                                ppas
                                where despesas.i_entidades = {entidade} and
                                despesas.ano_exerc = {ano} and
                                despesas.valor <> 0 and
                                despesas.portaria_func = 42 
                                and despesas.ano_exerc between ppas.i_exercicios and ppas.exerc_fin     		  
                                group by organograma, despesas.i_elementos, despesas.i_programas, despesas.i_proj_ativ,
                                                despesas.i_funcoes, despesas.i_subs, despesas.ano_exerc, despesas.i_entidades ) desp 
                            """
    return sql