# credores
# BuscaEhSalvaJsonSistemasContabil(token, url, 'credores', conn)

def credores(entidade = 1, ano = 2022):
    sql = f"""
            SELECT 
                        'credores' AS tipo_registro,
                    MD5(CONCAT(credor.cnpjCpf)) as HASH,	   
                    JSON_OBJECT(
                        'idIntegracao', MD5(CONCAT(credor.cnpjCpf)),     
                            'content',	
                                JSON_MERGE_PRESERVE( 					 	                  
                                JSON_OBJECT(
                                        'tipo', credor.tipo,
                                        'dataInclusao', credor.dataInclusao,
                                        'nome', credor.nome
                                ),
                                if(credor.tipo = 'FISICA', JSON_OBJECT('fisica', JSON_OBJECT('cpf', credor.cnpjCpf)), JSON_OBJECT()),
                                
                                if(credor.tipo = 'JURIDICA', JSON_OBJECT('juridica', 
                                        JSON_OBJECT('cnpj', credor.cnpjCpf, 'optanteSimples', JSON_EXTRACT(credor.optsimples,'$'))),
                                        JSON_OBJECT()),
                                        
                                    if(credor.id_logradouro IS NOT NULL AND credor.id_municipio IS NOT NULL,   
                                        JSON_OBJECT('enderecos', JSON_ARRAY(
                                            JSON_OBJECT(
                                                    'principal', TRUE,
                                                    'numero', 'S/N',
                                                    'municipio', JSON_OBJECT('id', cast(credor.id_municipio AS SIGNED)),
                                                    'logradouro', JSON_OBJECT('id', cast(credor.id_logradouro AS SIGNED))
                                                ) 
                                        )						 	 
                                        ),
                                        JSON_OBJECT()				 
                                    ) 					 
                            )
                        ) AS js,
                        json_object('cpfCnpj', credor.cnpjCpf)				
                FROM(SELECT 
                            MAX(credor.tipo) AS 'tipo',
                            MAX(credor.nome) AS 'nome',
                            credor.cnpjCpf AS 'cnpjCpf',
                            MAX(credor.dataInclusao) AS 'dataInclusao',
                            MAX(credor.optsimples) AS 'optsimples',
                            MAX(credor.id_municipio) AS 'id_municipio',
                            MAX(credor.id_logradouro) AS 'id_logradouro'		
                    FROM(SELECT 
                                if(credores.tipo_credor = 'F', 'FISICA', 'JURIDICA') AS 'tipo',
                                credores.nome AS 'nome',
                                coalesce(credores.cgc, credores.cpf) AS 'cnpjCpf',
                                'S/N' AS 'numero',
                                credores.data_inclusao_credor AS 'dataInclusao',
                                if(credores.optante_simples = 'N', 'false','true') AS 'optsimples',
                                
                                (SELECT regmun.id 
                                    FROM registro_lotes regmun
                                WHERE regmun.tipo_registro = 'municipios'
                                    AND regmun.JSON_store->>'$.content.uf' = credores.unidade_federacao
                                    AND regmun.JSON_store->>'$.content.nome' = credores.cidade) AS 'id_municipio',
                                
                                (SELECT MAX(reg.id)
                                    FROM registro_lotes reg 
                                    WHERE reg.tipo_registro = 'logradouros'
                                            AND reg.JSON_store->>'$.content.cep' = credores.cep	
                                            AND reg.JSON_store->>'$.content.nome' = LEFT(credores.endereco,50)
                                            AND reg.JSON_store->>'$.content.municipio.id' = 
                                            (SELECT regmun.id 
                                            FROM registro_lotes regmun
                                            WHERE regmun.tipo_registro = 'municipios'
                                                AND regmun.JSON_store->>'$.content.uf' = credores.unidade_federacao
                                                AND regmun.JSON_store->>'$.content.nome' = credores.cidade)) AS id_logradouro
                        FROM credores 
                        WHERE credores.tipo_credor IN ('F','J') 	
                                AND coalesce(credores.cgc, credores.cpf)  
                                AND NOT EXISTS(SELECT 1
                                                    FROM registro_lotes reg
                                                    WHERE reg.tipo_registro = 'credores'
                                                            and coalesce(reg.JSON_store->>'$.content.cpfCnpj',
                                                                            reg.JSON_store->>'$.content.fisica.cpf',
                                                                            reg.JSON_store->>'$.content.juridica.cnpj') = 
                                                                coalesce(credores.cgc, credores.cpf)) 
                                ) AS credor
                    GROUP BY credor.cnpjCpf ) AS credor
                """
    return sql