# transacoes-financeiras

def transacoes_financeiras_sql (entidade = 1, ano = 2022):
    sql = f"""
            SELECT 
                'transacoes-financeiras' AS tipo_registro,
            MD5(CONCAT(trsf.tipo)) as HASH,
            JSON_OBJECT(
                    'idIntegracao', MD5(CONCAT(trsf.tipo)),
                        'content', 				                  
                        JSON_OBJECT(
                                'tipo', trsf.tipo,							
                            'descricao', trsf.descricao                
                        )
                ) AS js,
                JSON_OBJECT('tipo', trsf.tipo) AS refdados 	
        FROM (select 'transacoesFinanceiras' AS tipo_registro, 1 AS sistema, 1 AS numero, 'Débito em conta' AS 'dsk1', 'Débito em conta' AS 'descricao',1 AS 'dsk2','DEBITO_AUTOMATICO' AS 'tipo' UNION 
                select 'transacoesFinanceiras' AS tipo_registro, 1 AS sistema, 2 AS numero, 'Outros' AS 'dsk1','Outros'  AS 'descricao',1  AS 'dsk2','ORDEM_BANCARIA' AS 'tipo' UNION 
                select 'transacoesFinanceiras' AS tipo_registro, 1 AS sistema, 3 AS numero, 'Inexistente' AS 'dsk1','Inexistente'  AS 'descricao' ,1  AS 'dsk2','INEXISTENTE' AS 'tipo' UNION 
                select 'transacoesFinanceiras' AS tipo_registro, 1 AS sistema, 4 AS numero, 'Crédito em Conta' AS 'dsk1','Crédito em Conta'  AS 'descricao',1  AS 'dsk2','CREDITO_BANCARIO' AS 'tipo' UNION 
                select 'transacoesFinanceiras' AS tipo_registro, 1 AS sistema, 5 AS numero, 'Caixa' AS 'dsk1','Caixa'  AS 'descricao',1  AS 'dsk2','DINHEIRO' AS 'tipo' UNION 
                select 'transacoesFinanceiras' AS tipo_registro, 1 AS sistema, 6 AS numero, 'Cheque' AS 'dsk1','Cheque' AS 'descricao',1  AS 'dsk2','CHEQUE' AS 'tipo' UNION 
                select 'transacoesFinanceiras' AS tipo_registro, 1 AS sistema, 7 AS numero, 'Transferência' AS 'dsk1','Transferência'  AS 'descricao',1  AS 'dsk2','TRANSFERENCIA' AS 'tipo') AS trsf 
        WHERE EXISTS(SELECT 1 
                        FROM registro_lotes reg 
                        WHERE reg.tipo_registro = 'transacoes-financeiras'	
                                AND coalesce(reg.JSON_store->>'$.content.tipo',
                                             reg.JSON_store->>'$.content.tipo.key') = trsf.tipo)
        """
    return sql
    