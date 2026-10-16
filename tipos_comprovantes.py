# tipos-comprovantes

def tipos_comprovantes_sql(entidade = 1, ano = 2022):
    sql = f"""
            SELECT 
                'tipos-comprovantes' AS tipo_registro,
                MD5(CONCAT(temp.chave_dsk1, temp.descDesk, temp.tipoCloud)) as HASH,	   
                JSON_OBJECT(
                    'idIntegracao', MD5(CONCAT(temp.chave_dsk1, temp.descDesk, temp.tipoCloud)),     
                        'content',					 	                  
                            JSON_OBJECT(
                                    'tipoPadrao', temp.tipoCloud,
                                'descricao',  temp.descDesk
                            )
                    ) AS js,
                    JSON_OBJECT('tipoPadrao', temp.tipoCloud )
              FROM (SELECT '1' as chave_dsk1,'Nota Fiscal' as descDesk, 'NOTA_FISCAL' as tipoCloud union 
                    SELECT '2' as chave_dsk1,'Recibo Comum' as descDesk, 'RECIBO' as tipoCloud union 
                    SELECT '7' as chave_dsk1,'Recibo de Repasse' as descDesk, 'RECIBO' as tipoCloud union 
                    SELECT '3' as chave_dsk1,'Bilhete de Passagem' as descDesk, 'BILHETE_PASSAGEM' as tipoCloud union 
                    SELECT '4' as chave_dsk1,'Folha de Pagamento' as descDesk, 'OUTROS' as tipoCloud union 
                    SELECT '5' as chave_dsk1,'Diárias' as descDesk, 'OUTROS' as tipoCloud union 
                    SELECT '6' as chave_dsk1,'Doctos Diversos' as descDesk, 'OUTROS' as tipoCloud union 
                    SELECT '8' as chave_dsk1,'Recibo de Pagamento Pessoal' as descDesk, 'RECIBO' as tipoCloud union 
                    SELECT '9' as chave_dsk1,'Conhecimento de Transp. de Cargas' as descDesk, 'CONHECIMENTO' as tipoCloud union 
                    SELECT '10' as chave_dsk1,'Guia de Recolhimento' as descDesk, 'GUIA_RECOLHIMENTO' as tipoCloud union 
                    SELECT '11' as chave_dsk1,'Extrato Bancário' as descDesk, 'OUTROS' as tipoCloud union 
                    SELECT '12' as chave_dsk1,'Fatura (telefonia, energia, água, correios e locação)' as descDesk, 'FATURA' as tipoCloud union 
                    SELECT '13' as chave_dsk1,'Apólice' as descDesk, 'OUTROS' as tipoCloud ) as temp 
            WHERE NOT EXISTS(SELECT 1 
                                    FROM registro_lotes reg
                                    WHERE reg.tipo_registro = 'tipos-comprovantes'
                                            AND reg.JSON_store->>'$.content.tipoPadrao.key' = temp.tipoCloud) """
    return sql
    
    

