# receitas-extras

def receitas_extras_sql (entidade = 1, ano = 2022):
    sql = f""" 
            SELECT 
                    recextras.tipo_registro AS tipo_registro,
                MD5(CONCAT(recextras.tipo_registro, recextras.sistema, recextras.chave_dsk1,
                                recextras.chave_dsk2, recextras.descricao, recextras.tipo)) as HASH,
                JSON_OBJECT(
                    'idIntegracao', MD5(CONCAT(recextras.tipo_registro, recextras.sistema, recextras.chave_dsk1,
                                                        recextras.chave_dsk2, recextras.descricao, recextras.tipo)),
                    'content', 				                  
                    JSON_OBJECT('tipo', recextras.tipo,
                                    'descricao', recextras.descricao
                            )
                ) AS js       
            FROM (
            SELECT 'receitas-extras' as tipo_registro,
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
            order by chave_dsk1 ) AS recextras
            WHERE NOT EXISTS(SELECT 1
                               FROM registro_lotes reg
                              WHERE reg.tipo_registro = 'receitas-extras'
                                    AND (reg.JSON_store->>'$.content.tipo' = recextras.tipo OR 
                                         reg.JSON_store->>'$.content.tipo.key' = recextras.tipo) 
                                    AND reg.JSON_store->>'$.content.descricao' = recextras.descricao)
            group by tipo_registro, sistema, chave_dsk1, chave_dsk2, descricao, tipo
            """
    return sql
    