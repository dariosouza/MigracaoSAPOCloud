# comprovantes

def comprovantes(entidade = 1, ano = 2022):
    sql = f"""
            SELECT 
                'comprovantes' AS tipo_registro,
                MD5(CONCAT(df.credor, df.numero, df.finalidade, df.data_vencimento, df.valor)) as HASH,	   
                JSON_OBJECT(
                    'idIntegracao', MD5(CONCAT(df.credor, df.numero, df.finalidade, df.data_vencimento, df.valor)),     
                        'content',					 	                  
                            JSON_OBJECT(
                                    'tipo', JSON_OBJECT('id', cast(df.id_tipo AS SIGNED)),
                                    'credor', JSON_OBJECT('id', cast(df.credor AS SIGNED)),
                                    'numero', df.numero,
                                    'data', df.data,
                                    'valorDesconto', df.valorDesconto,
                                    'finalidade', df.finalidade,
                                    'vencimentos', JSON_ARRAY(  
                                        JSON_OBJECT(
                                            'data', df.data_vencimento,
                                            'valor', df.valor 
                                        )
                                    ),
                                    'valor', df.valor,
                                    'classificacao', df.classificacao,
                                    'exercicio', df.ano_exerc
                            )
                    ) AS js,
                    JSON_OBJECT('docnumber', df.num_docto)
            FROM (SELECT 
                        dctos_fiscais.num_docto,
                        coalesce(dctos_fiscais.cgc, dctos_fiscais.cpf) AS 'doc', 
                        dctos_fiscais.ano_exerc, 
                        
                        if(EXISTS(SELECT 1
                                FROM prestacoes p
                                WHERE p.ano_exerc = dctos_fiscais.ano_exerc
                                    AND p.i_entidades = dctos_fiscais.i_entidades
                                    AND coalesce(p.i_ordens, p.i_restos) = dctos_fiscais.num_docto),
                        'COMPROVANTE_PRESTACOES', 'COMPROVANTE_COMPRAS') AS 'classificacao',
                        
                        (SELECT MAX(reg.id)
                            FROM registro_lotes reg
                            WHERE reg.tipo_registro = 'tipos-comprovantes'
                                    AND reg.JSON_store->>'$.content.tipoPadrao.key' = 
                                        (case dctos_fiscais.i_tipo_dcto_fiscal 
                                            when 1 then 'NOTA_FISCAL'
                                            when 2 then 'RECIBO' 	
                                            when 3 then 'BILHETE_PASSAGEM' 
                                            when 4 then 'OUTROS' 
                                            when 5 then 'OUTROS' 
                                            when 6 then 'OUTROS'
                                            when 7 then 'RECIBO' 
                                            when 8 then 'RECIBO' 
                                            when 9 then 'CONHECIMENTO' 
                                            when 10 then 'GUIA_RECOLHIMENTO' 
                                            when 11 then 'OUTROS' 
                                            when 12 then 'FATURA'  
                                            when 13 then 'OUTROS'
                                            END)) AS 'id_tipo',
                        
                        (SELECT MAX(reg.id)
                            FROM registro_lotes reg
                            WHERE reg.tipo_registro = 'credores'
                                    AND reg.refdados->>'$.cpfCnpj' =
                                        coalesce(dctos_fiscais.cgc, dctos_fiscais.cpf)) AS 'credor', 
                                                    
                        UPPER(if(dctos_fiscais.i_numero_dcto_fiscal = 'SN', 'S/N', dctos_fiscais.i_numero_dcto_fiscal)) AS 'numero',
                        dctos_fiscais.data_emissao AS 'data',
                        
                        0 AS 'valorDesconto',
                        coalesce(dctos_fiscais.historico_dcto_fiscal, 
                                    CONCAT(dctos_fiscais.emitente,' Doc Credor: ',
                                    coalesce(dctos_fiscais.cgc, dctos_fiscais.cpf))) AS 'finalidade',
                                    
                        dctos_fiscais.data_vencimento AS 'data_vencimento',
                        dctos_fiscais.valor_dcto_fiscal AS 'valor'		  	  
                            
                FROM dctos_fiscais 
                WHERE dctos_fiscais.i_entidades = {entidade} 
                        AND dctos_fiscais.ano_exerc = {ano}
                        AND coalesce(dctos_fiscais.cgc, dctos_fiscais.cpf) IS NOT NULL ) AS df
            WHERE df.credor IS NOT NULL and
            NOT EXISTS(SELECT 1 
                         FROM registro_lotes reg
                        WHERE reg.tipo_registro = 'comprovantes'
                              AND reg.JSON_store->>'$.content.tipo.id'	= df.id_tipo
                              AND reg.JSON_store->>'$.content.credor.id'	= df.credor
                              AND reg.JSON_store->>'$.content.numero'	= df.numero
                              AND reg.JSON_store->>'$.content.valor' = df.valor
                              AND reg.JSON_store->>'$.content.exercicio' = df.ano_exerc
                              AND (reg.JSON_store->>'$.content.classificacao.key' = df.classificacao OR 
                                   reg.JSON_store->>'$.content.classificacao' = df.classificacao)
                              AND reg.JSON_store->>'$.content.vencimentos[0].valor' = df.valor 
                              AND reg.JSON_store->>'$.content.vencimentos[0].data' = df.data_vencimento) 
 		 
    """
    return sql
    