# despesas-nao-previstas

def despesas_nao_previstas_sql(entidade = 1, ano = 2022):
    sql = f""" 
            SELECT 
                        desp.tipo_registro AS tipo_registro,
                    MD5(CONCAT('desp',desp.tipo_registro, desp.ano_exerc, desp.organograma, desp.natureza, 
                                    desp.funcao, desp.programas, desp.acao, desp.subfuncao, desp.localizador)) as HASH,
                    JSON_OBJECT(
                        'idIntegracao', MD5(CONCAT('desp',desp.tipo_registro, desp.ano_exerc, desp.organograma, desp.natureza, 
                                                            desp.funcao, desp.programas, desp.acao, desp.subfuncao, desp.localizador)),
                        'content', 				                  
                        JSON_OBJECT('funcao', JSON_OBJECT('id', CAST(desp.funcao AS SIGNED)),
                                            'programa', JSON_OBJECT('id', CAST(desp.programas AS SIGNED)),
                                            'natureza', JSON_OBJECT('id', CAST(desp.natureza AS SIGNED)),
                                            'organograma', JSON_OBJECT('id', CAST(desp.organograma AS SIGNED)),
                                            'exercicio', desp.ano_exerc,
                                            'acao', JSON_OBJECT('id', CAST(desp.acao AS SIGNED)),
                                            'localizador', JSON_OBJECT('id', CAST(desp.localizador AS SIGNED)),
                                            'subfuncao', JSON_OBJECT('id', CAST(desp.subfuncao AS SIGNED))
                                )
                    ) AS js
                FROM (SELECT  
                            'despesas-nao-previstas' as tipo_registro,	     
                        desp.ano_exerc,	      
                        
                        (SELECT cast(registro_lotes.id AS SIGNED)
                            FROM registro_lotes
                            WHERE registro_lotes.tipo_registro = 'organogramas' 
                                AND registro_lotes.json_store->>'$.content.numero' = 
                                concat(LPAD(desp.i_orgaos, 2, '0'),LPAD(desp.i_unidades, 3,'0'))
                                AND registro_lotes.json_store->>'$.content.configuracao.id' = 
                                CAST((SELECT max(reg.json_store->>'$.content.id')
                                        FROM registro_lotes reg
                                        WHERE reg.tipo_registro = 'configuracoes-organogramas'
                                            AND reg.json_store->>'$.content.descricao' LIKE '%{ano}%') AS SIGNED)) AS 'organograma',	      

                        (SELECT max(registro_lotes.id)
                                FROM registro_lotes, 
                                    elementos 
                            WHERE registro_lotes.tipo_registro = 'naturezas-despesas' 
                                        AND elementos.i_entidades = desp.i_entidades
                                        AND elementos.i_elementos = desp.i_elementos
                                        AND elementos.portaria = desp.ano_exerc
                                        AND registro_lotes.json_store->>'$.content.numero' = elementos.i_elementos) AS 'natureza', 

                        (SELECT max(registro_lotes.id)
                            FROM registro_lotes
                            WHERE registro_lotes.tipo_registro = 'funcoes' 
                                    AND registro_lotes.json_store->>'$.content.numero' = func.i_funcoes  
                                    AND registro_lotes.json_store->>'$.content.descricao' = func.descricao) AS 'funcao',

                            (SELECT max(registro_lotes.id)
                            FROM registro_lotes, 
                                    programas 
                            WHERE registro_lotes.tipo_registro = 'programas' 
                                    AND programas.i_entidades = desp.i_entidades 
                                    AND programas.i_programas = desp.i_programas
                                    AND programas.portaria_func = 42
                                    AND registro_lotes.json_store->>'$.content.numero' = programas.i_programas
                                    AND registro_lotes.json_store->>'$.content.descricao' = programas.descricao) AS 'programas',

                            (SELECT max(registro_lotes.id)
                                FROM registro_lotes, 
                                    proj_ativ,
                                        ppas pa  
                            WHERE registro_lotes.tipo_registro = 'acoes' 
                                        AND proj_ativ.i_proj_ativ = desp.i_proj_ativ
                                        AND proj_ativ.i_exercicios = desp.ano_exerc
                                        AND proj_ativ.i_ppas = pa.i_ppas 
                                        AND {ano} BETWEEN pa.i_exercicios AND pa.exerc_fin 
                                        AND registro_lotes.json_store->>'$.content.numero' = proj_ativ.i_acoes
                                        AND registro_lotes.json_store->>'$.content.descricao' = proj_ativ.descricao) AS 'acao',

                            (SELECT max(registro_lotes.id)
                                FROM registro_lotes, 
                                    subfuncoes  
                            WHERE registro_lotes.tipo_registro = 'subfuncoes' 
                                        AND subfuncoes.i_subfuncoes = subfunc.i_subfuncoes
                                        AND subfuncoes.i_atos = 42
                                        AND registro_lotes.json_store->>'$.content.numero' = subfuncoes.i_subfuncoes
                                        AND registro_lotes.json_store->>'$.content.descricao' = subfuncoes.descricao) AS 'subfuncao',

                            #select * from localizadores
                            #select * from ppas

                            (SELECT max(registro_lotes.id)
                            FROM registro_lotes, 
                                localizadores   
                        WHERE registro_lotes.tipo_registro = 'localizadores'
                                    AND registro_lotes.json_store->>'$.content.descricao' = trim(localizadores.descricao)
                                    AND registro_lotes.json_store->>'$.content.ppa.id' =  
                                        (SELECT max(registro_lotes.id)
                                            FROM registro_lotes, 
                                                ppas   
                                        WHERE registro_lotes.tipo_registro = 'parametros-ppa' 
                                                    AND registro_lotes.json_store->>'$.content.anoInicial' = ppas.i_exercicios 	 
                                                    AND registro_lotes.json_store->>'$.content.anoFinal' = ppas.exerc_fin
                                                    AND registro_lotes.id IS NOT NULL 
                                                    AND {ano} BETWEEN ppas.i_exercicios AND ppas.exerc_fin)) AS 'localizador'

                    FROM despesas desp join
                        elementos on (desp.i_entidades = elementos.i_entidades and 
                                                        desp.ano_exerc = elementos.portaria and
                                                        desp.i_elementos = elementos.i_elementos) join 
                        funcoes func on ((desp.i_funcoes = func.i_funcoes) and (desp.portaria_func = func.i_atos)) join
                        subfuncoes subfunc on ((desp.i_subs = subfunc.i_subfuncoes) and (desp.portaria_func = subfunc.i_atos)) join               
                        proj_ativ projAt on (
                                (desp.i_proj_ativ is null and 
                                desp.ano_exerc = projAt.i_exercicios and 
                                desp.pro_atv = substr(projAt.i_proj_ativ,1,1) and 
                                desp.numero_despesa = cast(substr(projAt.i_proj_ativ,2,3) as SIGNED)) or 
                                (desp.ano_exerc = projAt.i_exercicios and 
                                desp.i_proj_ativ = projAt.i_proj_ativ )) join
                        localizadores on (desp.i_localizadores = localizadores.i_localizadores),
                        (select i_ppas from ppas WHERE {ano} between ppas.i_exercicios and ppas.exerc_fin and dt_aprovacao is not null) tab 
                    where desp.i_entidades = {entidade}
                    and desp.ano_exerc = {ano}
                    and desp.valor = 0.00
                    and desp.i_elementos <> '00000000000000') desp
                WHERE NOT EXISTS(SELECT 1
                                    FROM registro_lotes 
                                WHERE registro_lotes.tipo_registro = 'despesas-nao-previstas'
                                        AND registro_lotes.json_store->>'$.content.funcao.id' = desp.funcao
                                        AND registro_lotes.json_store->>'$.content.programa.id' = desp.programas
                                        AND registro_lotes.json_store->>'$.content.natureza.id' = desp.natureza
                                        AND registro_lotes.json_store->>'$.content.organograma.id' = desp.organograma
                                        AND registro_lotes.json_store->>'$.content.acao.id' = desp.acao
                                        AND registro_lotes.json_store->>'$.content.localizador.id' = desp.localizador
                                        AND registro_lotes.json_store->>'$.content.subfuncao.id' = desp.subfuncao)
                GROUP BY desp.tipo_registro, desp.ano_exerc, desp.organograma, desp.natureza,
                            desp.funcao, desp.programas, desp.acao, desp.subfuncao, desp.localizador
            """
    return sql