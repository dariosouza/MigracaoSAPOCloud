# receitas-extras-exercicios

def receitas_extras_exercicios_sql (entidade = 1, ano = 2022):
    sql = f""" 
            SELECT 
                    recextexerc.tipo_registro AS tipo_registro,
                    MD5(CONCAT(recextexerc.receitaExtra, recextexerc.chave_dsk1, recextexerc.chave_dsk2, recextexerc.chave_dsk3, recextexerc.recur)) as HASH,
                    JSON_OBJECT(
                        'idIntegracao', MD5(CONCAT(recextexerc.receitaExtra, recextexerc.chave_dsk1,
                                                        recextexerc.chave_dsk2, recextexerc.chave_dsk3, recextexerc.recur)),
                        'content',
                        JSON_OBJECT('receitaExtra', JSON_OBJECT('id', CAST(recextexerc.receitaExtra AS SIGNED)),
                                        'exercicio', CAST( recextexerc.chave_dsk1 AS SIGNED),
                                        'recursos', (SELECT JSON_ARRAYAGG(JSON_OBJECT('id', 
                                                            (SELECT cast(max(reg.id) AS SIGNED)
                                                                FROM registro_lotes reg
                                                                WHERE reg.tipo_registro = 'recursos' 
                                                                        AND reg.JSON_store->>'$.content.numero' = CONCAT('1',lpad(recursos.i_recursos,3,'0'),'0000')
                                                                        AND reg.JSON_store->>'$.content.configuracaoRecurso.id' =
                                                                (SELECT max(reg.json_store->>'$.content.id')
                                                                    FROM registro_lotes reg
                                                                    WHERE reg.tipo_registro = 'configuracoes-recursos'
                                                                        AND reg.json_store->>'$.content.descricao' = 'Configuração Padrão'))))
                                                            FROM recursos 
                                                            WHERE FIND_IN_SET(recursos.i_recursos, recextexerc.recur)
                                                                    AND recursos.i_entidades = recextexerc.chave_dsk3))
                ) AS js     
            FROM ( select 'receitas-extras-exercicios' as tipo_registro,
                    1 sistema,
                    '{ano}' as chave_dsk1,
                    tab.chave_dsk1 as chave_dsk2,
                    tab.chave_dsk2 as chave_dsk3,  
                        
                        (SELECT max(reg.id)
                            FROM registro_lotes reg
                            WHERE reg.tipo_registro = 'receitas-extras'
                                    AND (reg.JSON_store->>'$.content.tipo' = max(tab.tipo) OR 
                                        reg.JSON_store->>'$.content.tipo.key' = max(tab.tipo)) 
                                    AND reg.JSON_store->>'$.content.descricao' = max(tab.descricao)) AS 'receitaExtra',
                                    
                        GROUP_CONCAT(distinct lmi2.i_recursos ) AS recur		 
                from lancamentos_manuais_itens lmi2 join
                    contas c2 on (c2.i_entidades = lmi2.i_entidades and 
                                    c2.i_plano_contas = lmi2.i_plano_contas and
                                    c2.i_contas = lmi2.i_contas and
                                    c2.bancaria <> 'N') JOIN
                                    
                    (SELECT 'receitas-extras' as tipo_registro,
                                    1 AS sistema,         
                                c.i_contas as chave_dsk1, 
                                c.i_entidades as chave_dsk2,
                                c.descricao as descricao,
                                if(dbf_cta_getclassifmasc(c.i_entidades, c.i_plano_contas, lmi.ano_exerc, 'C_DDO', c.mascara) = 1,
                                    'DEPOSITO', 'TRANSFERENCIA_FINANCEIRA') as tipo,
                                lmi.i_lancamentos_manuais     
                            from lancamentos_manuais_itens lmi join
                                lancamentos_manuais lm on(lm.ano_exerc = lmi.ano_exerc and 
                                                        lm.i_entidades = lmi.i_entidades and 
                                                        lm.i_lancamentos_manuais = lmi.i_lancamentos_manuais) join
                                eventos_contabeis ec on(ec.ano_exerc = lmi.ano_exerc and 
                                                        ec.i_entidades = lmi.i_entidades and 
                                                        ec.i_eventos_contabeis = lmi.i_eventos_contabeis and
                                                        ec.i_tipos_lanctos_ctb not in (0,1,4,5)) join
                                contas c on (c.i_entidades = lmi.i_entidades and 
                                            c.i_plano_contas = lmi.i_plano_contas and
                                            c.i_contas = lmi.i_contas)
                        where lmi.i_entidades = {entidade} and
                                lmi.ano_exerc = {ano} AND 
                            (dbf_cta_getclassifmasc(c.i_entidades, c.i_plano_contas, lmi.ano_exerc, 'C_TRANSF_FINANC_CONCEDIDA', c.mascara) = 1 or
                                dbf_cta_getclassifmasc(c.i_entidades, c.i_plano_contas, lmi.ano_exerc, 'C_TRANSF_FINANC_RECEBIDA', c.mascara) = 1 or 
                                dbf_cta_getclassifmasc(c.i_entidades, c.i_plano_contas, lmi.ano_exerc, 'C_DDO', c.mascara) = 1) AND 
                            (select COUNT(*)            
                                from lancamentos_manuais_itens 
                                where ano_exerc = lmi.ano_exerc and 
                                        i_entidades = lmi.i_entidades AND 
                                        i_lancamentos_manuais = lmi.i_lancamentos_manuais) = 2 and 
                                exists(select 1      
                                        from lancamentos_manuais_itens lancItens join
                                            contas on (contas.i_entidades = lancItens.i_entidades and 
                                                        contas.i_plano_contas = lancItens.i_plano_contas and
                                                        contas.i_contas = lancItens.i_contas)
                                        where lancItens.ano_exerc = lmi.ano_exerc and 
                                            lancItens.i_entidades = lmi.i_entidades AND 
                                            lancItens.i_lancamentos_manuais = lmi.i_lancamentos_manuais AND 
                                            contas.bancaria <> 'N')
                        group by tipo_registro, sistema, chave_dsk1, chave_dsk2, descricao, tipo, lmi.i_lancamentos_manuais
                        order by chave_dsk1 
                
                ) as tab on (lmi2.ano_exerc = {ano} and 
                            lmi2.i_entidades = {entidade} and 
                            lmi2.i_lancamentos_manuais in (tab.i_lancamentos_manuais))
                group by tipo_registro, sistema, chave_dsk1, chave_dsk2, chave_dsk3 ) recextexerc 
            """
    return sql