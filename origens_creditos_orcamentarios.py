# origens-creditos-orcamentarios

def origens_creditos_orcamentarios_sql (entidade = 1, ano = 2022):
    sql = f""" 
                SELECT 
                        orgcredorc.tipo_registro AS tipo_registro,
                        MD5(CONCAT(orgcredorc.tipo_registro, orgcredorc.sistema, orgcredorc.chave_dsk1,
                                    orgcredorc.descricao, orgcredorc.tipo_padrao)) as HASH,
                        JSON_OBJECT(
                            'idIntegracao', MD5(CONCAT(orgcredorc.tipo_registro, orgcredorc.sistema, orgcredorc.chave_dsk1,
                                                                orgcredorc.descricao, orgcredorc.tipo_padrao)),
                            'content',
                            JSON_OBJECT('enquadramento', orgcredorc.tipo_padrao,
                                            'descricao', orgcredorc.descricao
                                    )
                        ) AS js
                FROM (select
                            'origens-creditos-orcamentarios' as tipo_registro, 
                            1 as sistema, 
                            chave_dsk1,
                            descricao,
                            tipo_padrao
                            from (select 1 as chave_dsk1, 'Anulação de dotação' as descricao, 'ANULACAO_DOTACAO' as tipo_padrao union all
                                    select 2 as chave_dsk1, 'Superávit financeiro' as descricao, 'SUPERAVIT_FINANCEIRO_EXERCICIO_ANTERIOR' as tipo_padrao union all
                                    select 3 as chave_dsk1, 'Excesso de arrecadação' as descricao, 'EXCESSO_ARRECADACAO' as tipo_padrao union all
                                    select 4 as chave_dsk1, 'Operações de crédito' as descricao, 'OPERACAO_CREDITO' as tipo_padrao union all
                                    select 5 as chave_dsk1, 'Dotação transferida' as descricao, 'ANULACAO_DOTACAO' as tipo_padrao union all
                                    select 7 as chave_dsk1, 'Auxílios e Convênios' as descricao, 'EXCESSO_ARRECADACAO' as tipo_padrao union all
                                    select 6 as chave_dsk1, 'Doações' as descricao, 'EXCESSO_ARRECADACAO' as tipo_padrao union all
                                    select 8 as chave_dsk1, 'Convênio' as descricao, 'EXCESSO_ARRECADACAO' as tipo_padrao union all
                                    select 9 as chave_dsk1, 'Art. 166, § 8° da CF' as descricao, 'RECURSOS_ORIUNDOS_CREDITO' as tipo_padrao union all
                                    select 0 as chave_dsk1, 'Reserva de Contingência' as descricao, 'RESERVA_CONTINGENCIA' as tipo_padrao
                                ) as temp
                        ) AS orgcredorc
                    WHERE NOT EXISTS(SELECT 1
                                    FROM registro_lotes reg
                                    WHERE reg.tipo_registro = 'origens-creditos-orcamentarios'
                                            AND (reg.JSON_store->>'$.content.enquadramento.key' = orgcredorc.tipo_padrao
                                                OR reg.JSON_store->>'$.content.enquadramento' = orgcredorc.tipo_padrao)
                                            AND reg.JSON_store->>'$.content.descricao' = orgcredorc.descricao)  """
    return sql