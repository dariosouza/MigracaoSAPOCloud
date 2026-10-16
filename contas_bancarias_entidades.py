# contas-bancarias-entidades

def contas_bancarias_entidades_sql (entidade = 1, idTipoAplicacao = 21980):
    sql = f"""SELECT 
                    'contas-bancarias-entidades' AS tipo_registro,
                    MD5(CONCAT(conta.numero, conta.digito, conta.agencia, conta.banco)) as HASH,	   
                    JSON_OBJECT(
                            'idIntegracao', MD5(CONCAT(conta.numero, conta.digito, conta.agencia, conta.banco) ),     
                                'content',
                                    JSON_MERGE_PRESERVE(					 		                  
                                    JSON_OBJECT(						 	  
                                            'numero', conta.numero,
                                            'digito', conta.digito,							
                                            'agencia', JSON_OBJECT('id', CAST(conta.agencia AS SIGNED)),
                                            'banco', JSON_OBJECT('id', CAST(conta.banco AS SIGNED)),
                                            'descricao', conta.descricao,
                                        
                                            'tiposContas', (SELECT JSON_ARRAYAGG(JSON_OBJECT('tipo', if(cc.mascara like '1111150%','POUPANCA','CORRENTE')))  
                                                                    FROM contas cc 
                                                                    WHERE cc.i_entidades = 1 
                                                                            AND find_in_set(cc.i_contas, idcontas) 
                                                                    GROUP BY cc.tipo_conta)								               				                 
                                    ),
                                    if(conta.datafinal IS NOT NULL, JSON_OBJECT('vigencias', 
                                            JSON_ARRAY(JSON_OBJECT('dataInicial', conta.datainicial,
                                                                        'motivoFinal',
                                                                        'Inativação da conta bancária',
                                                                        'dataFinal', conta.datafinal))),JSON_OBJECT()),
                                                                        
                                        if(conta.datafinal IS NULL, JSON_OBJECT('vigencias', 
                                            JSON_ARRAY(JSON_OBJECT('dataInicial', conta.datainicial))),JSON_OBJECT()),
                                            
                                        
                                        if(EXISTS(SELECT 1 
                                                        FROM contas cc 
                                                        WHERE cc.i_entidades = 1 
                                                                AND FIND_IN_SET(cc.i_contas, idcontas)   
                                                                AND cc.mascara like '1111150%') AND conta.datafinal IS NOT NULL,
                                            JSON_OBJECT('vigenciasTipoAplicacao', 
                                            JSON_ARRAY(JSON_OBJECT('dataInicial', conta.datainicial,
                                                                        'motivoFinal','Inativação da vigência bancária',
                                                                            'tipoAplicacao', JSON_OBJECT('id', {idTipoAplicacao}), /*Código estatico dessa variavel*/
                                                                        'dataFinal', conta.datafinal))),JSON_OBJECT()),
                                                                                                                                
                                        if(EXISTS(SELECT 1 
                                                        FROM contas cc 
                                                        WHERE cc.i_entidades = 1 
                                                                AND FIND_IN_SET(cc.i_contas, idcontas)   
                                                                AND cc.mascara like '1111150%') AND conta.datafinal IS NULL,
                                            JSON_OBJECT('vigenciasTipoAplicacao', 
                                            JSON_ARRAY(JSON_OBJECT('tipoAplicacao', JSON_OBJECT('id', {idTipoAplicacao}), /*Código estatico dessa variavel*/
                                                                            'dataInicial', conta.datainicial))),JSON_OBJECT())
                                        
                                )
                        ) AS js,
                        JSON_OBJECT('i_entidades', 1, 'i_contas', idcontas) 
                FROM (SELECT 
                        ccb.numero,
                        ccb.digito,
                        ccb.agencia,
                        ccb.banco,
                        max(ccb.descricao) AS descricao,
                        MIN(ccb.dataInicial) AS datainicial,
                        MAX(ccb.dataFinal) AS datafinal,
                        GROUP_CONCAT(ccb.idconta) AS idcontas
                FROM(SELECT 
                            SUBSTRING_INDEX(contas.conta_banco, '-', 1) AS 'numero',
                            coalesce(SUBSTRING_INDEX(contas.conta_banco, '-', -1),'X') AS 'digito', 
                            contas.i_contas AS 'idconta',
                            contas.descricao AS 'descricao',
                            
                            (SELECT reg.id
                                FROM registro_lotes reg
                                WHERE reg.tipo_registro = 'agencias-bancarias'					
                                        AND reg.JSON_store->>'$.content.numero' = agencias.i_agencias
                                        AND reg.JSON_store->>'$.content.digito' = agencias.dv_agencia
                                        AND reg.JSON_store->>'$.content.banco.id' = 
                                        (SELECT regbb.id
                                        FROM registro_lotes regbb
                                        WHERE regbb.tipo_registro = 'bancos'
                                                AND regbb.json_store->>'$.content.numero' = LPAD(bancos.numero,3,'0'))) AS 'agencia',
                                        
                            (SELECT reg.id
                                FROM registro_lotes reg 
                                WHERE reg.tipo_registro = 'bancos'
                                        AND reg.json_store->>'$.content.numero' = LPAD(bancos.numero,3,'0')) AS 'banco',					
                                                        
                            contas.inclusao AS 'dataInicial',
                            contas.data_inativacao AS 'dataFinal'
                            
                    FROM contas, 
                            agencias,
                            bancos 
                    WHERE contas.i_entidades = {entidade} 
                            AND contas.i_bancos IS NOT NULL
                            AND contas.i_agencias = agencias.i_agencias
                            AND contas.i_entidades = bancos.i_entidades 
                            AND contas.i_bancos = bancos.i_bancos ) AS ccb
                WHERE NOT EXISTS(SELECT 1
                                        FROM registro_lotes reg 
                                        WHERE reg.tipo_registro = 'contas-bancarias-entidades' 
                                                AND reg.JSON_store->>'$.content.banco.id' = ccb.banco 
                                                AND reg.JSON_store->>'$.content.agencia.id' = ccb.agencia
                                                AND reg.JSON_store->>'$.content.numero' = ccb.numero
                                                AND reg.JSON_store->>'$.content.digito' = ccb.digito) 
                GROUP BY ccb.numero, ccb.digito, ccb.agencia, ccb.banco 
                ORDER BY ccb.numero, ccb.digito, ccb.agencia ) AS conta 
            """
    return sql
    