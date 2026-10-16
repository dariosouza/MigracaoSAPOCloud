# retencoes

def retencoes (entidade = 1, ano = 2022):
    sql = f"""
            SELECT 
                'retencoes' AS tipo_registro,
                MD5(CONCAT(rettemp.descConta, rettemp.tipo, rettemp.pagamentoAntecipado)) as HASH,	   
                JSON_OBJECT(
                    'idIntegracao', MD5(CONCAT(rettemp.descConta, rettemp.tipo, rettemp.pagamentoAntecipado)),     
                        'content',					 	                  
                            JSON_OBJECT(
                                    'pagamentoAntecipado', JSON_EXTRACT(rettemp.pagamentoAntecipado,'$'),
                                'tipo', rettemp.tipo,
                                'descricao', rettemp.descConta
                            )
                    ) AS js
                FROM(select 
                            if(d.i_rubricas is NULL, c.descricao, r.descricao) as descConta,            
                            if(d.tipo_desconto = 'C', 'EXTRAORCAMENTARIA','ORCAMENTARIA') as tipo,       		        
                            coalesce(if(if(d.tipo_desconto = 'C', 'EXTRAORCAMENTARIA','ORCAMENTARIA')/*tipo*/ = 'EXTRAORCAMENTARIA' and
                                                dbf_cta_getclassifmasc(d.i_entidades, c.i_plano_contas, d.ano_exerc, 'C_PAGAMENTOS_ANTECIPADOS', 
                                                if(d.i_rubricas is NULL, c.mascara, r.i_rubricas)/*refContas*/) = 1,   
                                    'true','false'),'false') as pagamentoAntecipado			  	                      
                    from descontos d left join 
                            contas c on (d.i_entidades = c.i_entidades and
                                                d.i_contas = c.i_contas ) left join 
                        rubricas r on (d.i_entidades = r.i_entidades and
                                                d.i_rubricas = r.i_rubricas and 
                                                d.portaria_rubr = r.portaria_rubr) 
                    where d.ano_exerc = {ano} and
                          d.i_entidades = {entidade} 
                            
                    UNION ALL 
                    
                    select       
                    contas.descricao as descConta,
                    'EXTRAORCAMENTARIA' as tipo,       
                    if(dbf_cta_getclassifmasc(despexs.i_entidades, contas.i_plano_contas, despexs.ano_exerc,
                        'C_PAGAMENTOS_ANTECIPADOS', contas.mascara) = 1, 'true', 'false') as pagamentoAntecipado                      
                    from despexs join contas 
                            on despexs.i_entidades = contas.i_entidades 
                            and despexs.i_contas = contas.i_contas                           
                    where despexs.i_entidades = {entidade} and
                            despexs.ano_exerc = {ano} 
                ) AS rettemp
            WHERE NOT EXISTS(SELECT 1
                               FROM registro_lotes reg
                              WHERE reg.tipo_registro = 'retencoes'
                                    AND reg.JSON_store->>'$.content.tipo' = rettemp.tipo
                                    AND reg.JSON_store->>'$.content.descricao' = rettemp.descConta
                                    AND reg.JSON_store->>'$.content.pagamentoAntecipado' = rettemp.pagamentoAntecipado)
            GROUP BY rettemp.descConta, rettemp.tipo, rettemp.pagamentoAntecipado """
    return sql
    