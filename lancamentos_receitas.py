# lancamentos-receitas
import mysql.connector
from tqdm import tqdm
import json

def lancamentos_receitas_rater (entidade = 1, ano = 2022, i_lotes_atr = 0, identity = 300488):
    sql = f"""
                SELECT 
                    'arrecadacoes-orcamentarias' AS tipo_registro,
                    MD5(CONCAT(arrec.i_arrecadacoes, arrec.exercicio, arrec.i_entidades)) as HASH,	   
                    JSON_OBJECT(
                        'idIntegracao', MD5(CONCAT(arrec.i_arrecadacoes, arrec.exercicio, arrec.i_entidades)),     
                            'content',					 	                  
                                JSON_OBJECT(					 	  
                                    'exercicio', arrec.exercicio,
                                        'data', arrec.data,
                                        'transacaoFinanceira', JSON_OBJECT('id', arrec.transacaoFinanceira),
                                        'contaBancaria', JSON_OBJECT('id', arrec.id_contaBancaria ),
                                        'valor', arrec.valor - arrec.valordeducao,
                                        'especificacao', arrec.especificacao,
                                        'tipoConta', arrec.tipoConta,
                                        'validaSaldo', JSON_EXTRACT(arrec.validaSaldo, '$'),						  							  								  					  						   						  						  						  
                                        'receitas', JSON_ARRAY(						  
                                            JSON_OBJECT(						  	   	
                                                    'receita', JSON_OBJECT('id', busca_id_receita_loa(arrec.entidade,
                                                                                                                    arrec.id_recurso,
                                                                                                                    arrec.exercicio,
                                                                                                                    arrec.loa, 
                                                                                                                    id_receita, 
                                                                                                                    organograma)),
                                                    'lancada', JSON_EXTRACT(arrec.lancada, '$'), 
                                                    'valor', arrec.valor, 
                                                    'recursos', JSON_ARRAY(
                                                        JSON_OBJECT(
                                                            'recurso', JSON_OBJECT('id', arrec.id_recurso ),
                                                            'valor', arrec.valor 										
                                                        )																																																		
                                                    ),								

                                                    'deducoes',
                                                    (SELECT 
                                                        JSON_ARRAYAGG(
                                                            JSON_OBJECT('deducao', JSON_OBJECT('id', deduc.id_deducao),
                                                                        'valor', deduc.valor,
                                                                            'recursos', JSON_ARRAY(
                                                                                JSON_OBJECT(
                                                                                    'recurso', JSON_OBJECT('id', deduc.id_cloud_recurso),
                                                                                    'valor', deduc.valor
                                                                                )
                                                                            )			
                                                            )
                                                        )													
                                                    FROM(SELECT 	
                                                            (SELECT CAST(MAX(reg.id) AS SIGNED)
                                                                FROM registro_lotes reg			 	 		
                                                                WHERE reg.tipo_registro = 'deducoes-receitas'
                                                                        AND reg.id IS NOT NULL
                                                                        AND coalesce(reg.json_Store->>'$.content.tipo.key',
                                                                                        reg.json_Store->>'$.content.tipo') = 
                                                                        (SELECT COALESCE(MAX((case tipo_deducao.tipo_stn
                                                                                                when 1 then 'RENUNCIA'
                                                                                                when 2 then 'RESTITUICOES'
                                                                                                when 3 then 'DESCONTOS_CONCEDIDOS'
                                                                                                when 5 then 'FUNDEB'
                                                                                                when 6 then 'COMPENSACOES'
                                                                                                when 8 then 'RETIFICACOES'
                                                                                                when 9 then 'OUTRAS_DEDUCOES'
                                                                                                ELSE 'OUTRAS_DEDUCOES' END)),
                                                                                                    if(rubricas.retencao_fundef = 'S', 'FUNDEB', 'OUTRAS_DEDUCOES'))
                                                                            FROM tipo_deducao 
                                                                            WHERE tipo_deducao.i_entidades = arrecadacoes.i_entidades
                                                                                    AND tipo_deducao.ano_exerc = arrecadacoes.ano_exerc
                                                                                    AND receitas.i_tipo_deducao = receitas.i_tipo_deducao)) AS 'id_deducao',			 						   								   
                                                                                    busca_id_recurso (arrecadacoes.i_entidades, COALESCE(receitas.i_recursos, 10),  'N') AS 'id_cloud_recurso',
                                                                                    arrecadacoes.valor     			          	    
                                                                            FROM arrecadacoes
                                                                            INNER JOIN rubricas ON (arrecadacoes.i_entidades = rubricas.i_entidades AND 
                                                                                                        arrecadacoes.portaria_rubr = rubricas.portaria_rubr AND 
                                                                                                    arrecadacoes.i_rubricas = rubricas.i_rubricas)	
                                                                                                                
                                                                            LEFT JOIN receitas ON (arrecadacoes.ano_exerc = receitas.ano_exerc AND 
                                                                                                    arrecadacoes.i_entidades = receitas.i_entidades AND 
                                                                                                    arrecadacoes.portaria_rubr = receitas.portaria_rubr AND 
                                                                                                    arrecadacoes.i_rubricas = receitas.i_rubricas)
                                                                            WHERE arrecadacoes.i_entidades = arrec.i_entidades
                                                                                    AND arrecadacoes.ano_exerc = arrec.exercicio	                  
                                                                                    AND arrecadacoes.i_lote_arr = arrec.i_lote_arr
                                                                                    AND if((arrecadacoes.i_rubricas LIKE '9%' AND arrecadacoes.i_rubricas NOT LIKE '999%') OR
                                                                                            arrecadacoes.i_rubricas LIKE '49%', 'N', 'S') = 'N'   ) AS deduc) 	
                                                                                                                                                                        
                                                )
                                        )						  				  						  
                                )
                        ) AS js	 		 	 				
                FROM( SELECT 
                            arrecadacoes.i_arrecadacoes,
                            arrecadacoes.i_entidades,  
                            arrecadacoes.i_lote_arr, 
                            busca_id_conta_bancaria(agencias.i_agencias, agencias.dv_agencia, agencias.i_bancos, contas.conta_banco) AS 'id_contaBancaria',
                            
                            #select * from arrecadacoes
                            arrecadacoes.i_rubricas AS 'natureza_receita',
                            
                            (SELECT COALESCE(SUM(arr.valor),0)
                                FROM arrecadacoes arr 
                            WHERE arr.i_entidades = arrecadacoes.i_entidades
                                    AND arr.ano_exerc = arrecadacoes.ano_exerc 
                                    AND arr.i_lote_arr = arrecadacoes.i_lote_arr 
                                    AND if((arr.i_rubricas LIKE '9%' AND arr.i_rubricas NOT LIKE '999%') OR 
                                                arr.i_rubricas LIKE '49%', 'N', 'S') = 'N') AS 'valordeducao',
                                
                            (SELECT lc.data_lancamento
                                FROM lancamentos lc
                            WHERE lc.ano_exerc = arrecadacoes.ano_exerc
                                    AND lc.i_entidades = arrecadacoes.i_entidades 
                                    AND lc.i_arrecadacoes = arrecadacoes.i_arrecadacoes
                                    AND lc.i_lote_arr = arrecadacoes.i_lote_arr
                                    AND lc.i_contas = contas_lotes.i_contas) AS 'data',
                                
                            CONCAT(lote_arr.descricao, ' / ', arrecadacoes.descricao)  AS 'especificacao',
                            
                            (SELECT CAST(MAX(reg.id) AS SIGNED)
                            FROM registro_lotes reg
                            WHERE reg.tipo_registro = 'transacoes-financeiras'
                                    AND reg.JSON_store->>'$.content.descricao' = 
                                            if(contas.bancaria = 'N','Inexistente','Crédito em Conta')) AS 'transacaoFinanceira',
                                                
                            arrecadacoes.valor AS 'valor',
                            if(arrecadacoes.tipo_arrecadacao = 'N', 'false', 'true') AS 'validaSaldo',
                                
                            busca_id_receita(arrecadacoes.i_rubricas, CONCAT('Portaria da Receita - ', arrecadacoes.ano_exerc)) AS 'id_receita',	
                            
                            (SELECT reg.id
                            FROM registro_lotes reg	
                            WHERE reg.tipo_registro = 'parametros-loa'
                                AND reg.JSON_store->>'$.content.exercicio' = receitas.ano_exerc) AS 'loa',
                                
                        {identity} AS 'entidade',
                        
                        (SELECT cast(reg.id AS SIGNED)
                            FROM registro_lotes reg			  	 		 
                            WHERE reg.tipo_registro = 'organogramas' 
                                AND reg.json_store->>'$.content.numero' = 
                                CONCAT(LPAD(receitas.i_orgaos, 2, '0'),LPAD(receitas.i_unidades, 3,'0')) 
                                AND reg.json_store->>'$.content.configuracao.id' = 
                                CAST((SELECT max(reg.json_store->>'$.content.id')
                                        FROM registro_lotes reg			  	 		 
                                        WHERE reg.tipo_registro = 'configuracoes-organogramas'
                                            AND reg.json_store->>'$.content.descricao' LIKE '%2022%') AS SIGNED) )  AS 'organograma',
                                
                            COALESCE(CONCAT('1', LPAD(receitas.i_recursos, 3, '0'), '0000'), '10100000') AS 'recurso_original',							
                                    
                            busca_id_recurso (arrecadacoes.i_entidades, receitas.i_recursos, 'N') AS 'id_recurso',
                            
                            if(contas.bancaria = 'P', 'POUPANCA', 'CORRENTE') as tipoConta,
                                        
                            'false' AS 'lancada',	
                            arrecadacoes.ano_exerc AS 'exercicio' 	
                                    
                    FROM arrecadacoes
                        INNER JOIN lote_arr ON (arrecadacoes.i_entidades = lote_arr.i_entidades AND 
                                                    arrecadacoes.ano_exerc = lote_arr.ano_exerc AND 
                                                        arrecadacoes.i_lote_arr = lote_arr.i_lote_arr)
                        INNER JOIN contas_lotes ON (lote_arr.i_entidades = contas_lotes.i_entidades AND 
                                                            lote_arr.ano_exerc = contas_lotes.ano_exerc AND 
                                                            lote_arr.i_lote_arr = contas_lotes.i_lote_arr)
                        INNER JOIN contas ON (contas_lotes.i_entidades = contas.i_entidades AND 
                                                    contas_lotes.i_contas = contas.i_contas)
                        INNER JOIN agencias ON (contas.i_agencias = agencias.i_agencias AND 
                                                    contas.i_agencias = agencias.i_agencias)
                        INNER JOIN receitas ON (arrecadacoes.ano_exerc = receitas.ano_exerc AND 
                                                arrecadacoes.i_entidades = receitas.i_entidades AND 
                                                arrecadacoes.portaria_rubr = receitas.portaria_rubr AND 
                                                arrecadacoes.i_rubricas = receitas.i_rubricas)
                        INNER JOIN lancamentos force index(idx_lanc)
                                                    on lancamentos.ano_exerc = arrecadacoes.ano_exerc
                                                    and lancamentos.i_entidades = arrecadacoes.i_entidades
                                                    and lancamentos.i_arrecadacoes = arrecadacoes.i_arrecadacoes
                                                    and lancamentos.i_lote_arr = arrecadacoes.i_lote_arr
                                                    and lancamentos.i_contas = contas_lotes.i_contas
                        WHERE arrecadacoes.i_entidades = {entidade} 
                                AND arrecadacoes.ano_exerc = {ano} 
                                AND arrecadacoes.i_lote_arr IN ({i_lotes_atr})
                                AND if((arrecadacoes.i_rubricas LIKE '9%' AND arrecadacoes.i_rubricas not LIKE '999%') OR
                                            arrecadacoes.i_rubricas LIKE '49%', 'N', 'S') = 'S' /*Apenas para rubricas arrecadação*/ ) AS arrec
                """
    return sql
    
def processa_lancamento_receita(conn = None, entidade = 1, ano = 2022):
        
    delete = f"""
            SELECT 	
                JSON_ARRAYAGG(	 
                    JSON_OBJECT(
                    'idIntegracao', MD5(id),
                        'content',					 	                  
                            JSON_OBJECT(					 	  
                            'exercicio', CAST(json_store->>'$.content.exercicio' AS SIGNED)
                            ),
                    'idGerado', JSON_OBJECT('id', CAST(id AS SIGNED))
                    )
                )	                 
        FROM registro_lotes 
        WHERE tipo_registro = 'arrecadacoes-orcamentarias'
                AND CAST(json_store->>'$.content.exercicio' AS SIGNED) = {ano}
                AND id IS NOT NULL                 
    """        
    
    createtable = """
                    CREATE TABLE arrecadacoes_orcamentarias (
                        tipo_registro varchar(120),
                        hash_v varchar(64),
                        json_store json 
                    ); 
                """       
    ##############################
    cuexetbl =  conn.cursor()
    cuexetbl.execute(createtable)
    cuexetbl.close() 
    ##############################   
    
    result = []    
    sql = f"""SELECT i_entidades, ano_exerc, i_lote_arr FROM lote_arr WHERE i_entidades = {entidade} AND ano_exerc = {ano}"""
    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute(sql)
    lotes_att = cursor.fetchall()
    totreg = cursor.rowcount
    cursor.close()        
        
    with tqdm(total=totreg, unit='B', unit_scale=True, desc="Processando lotes arrecadacao..", ncols=120) as pbar:            
        for row in lotes_att:
            selcSQL = lancamentos_receitas_rater(entidade, ano, row["i_lote_arr"])
            cur = conn.cursor()
            cur.execute(selcSQL)
            for idx in cur.fetchall():
                js = json.loads(idx[2])
                for rec in js.get('content', {}).get('receitas', []):
                    if rec.get('deducoes') is None:
                       rec.pop('deducoes')
                result.append({'tipo_registro': idx[0], 'HASH': idx[1], 'js': json.dumps(js) })
            cur.close()
            pbar.update(1)
        curinsert = conn.cursor(dictionary=True)
        for ln in result:
            sqlinsert = """INSERT INTO  arrecadacoes_orcamentarias (tipo_registro, hash_v, json_store) values (%s, %s, %s);"""            
            curinsert.execute( sqlinsert,( ln["tipo_registro"] , ln["HASH"], ln["js"] ))
        curinsert.close()
        conn.commit()
        
    return "select * from arrecadacoes_orcamentarias"
        