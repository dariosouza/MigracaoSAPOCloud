# organogramas

def organogramas_sql (entidade = 1, ano = 2022):

	sql = f"""SELECT 
					'organogramas' AS tipo_registro,
					MD5(CONCAT(organ.numero, organ.descricao, organ.tipoAdministracao, organ.configuracao)) as HASH,
					JSON_OBJECT(
							'idIntegracao', MD5(CONCAT(organ.numero, organ.descricao, organ.tipoAdministracao, organ.configuracao)),
								'content', 				                  
								JSON_OBJECT(						
									'tipoAdministracao', JSON_OBJECT('id', CAST(organ.tipoAdministracao AS SIGNED)),
									'configuracao', JSON_OBJECT('id', CAST(organ.configuracao AS SIGNED)),
									'numero', organ.numero,
									'descricao', organ.descricao
								)
						) AS js 	
				FROM (SELECT 
					concat(substring(organogramas.i_organogramas, 1, 2),'0',substring(organogramas.i_organogramas, 3, 2)) AS 'numero', 
					organogramas.descricao AS 'descricao',
					(SELECT reg.json_store->>'$.content.id'
							FROM registro_lotes reg,
									tipos_adm 
						WHERE reg.tipo_registro = 'tipos-administracoes'		 
								AND reg.json_store->>'$.content.descricao' = tipos_adm.descricao 
								AND tipos_adm.i_tipos_adm = organogramas.i_tipos_adm) AS 'tipoAdministracao',
						(SELECT max(reg.json_store->>'$.content.id')
							FROM registro_lotes reg			  	 		 
							WHERE reg.tipo_registro = 'configuracoes-organogramas'
									AND reg.json_store->>'$.content.descricao' LIKE '%{ano}%') AS 'configuracao'    						 
				FROM organogramas,
					exerc_entid
				WHERE organogramas.i_config_organ = exerc_entid.i_config_organ 
					and exerc_entid.i_entidades = {entidade}
					AND exerc_entid.i_exercicios = {ano} ) AS organ 
				WHERE NOT EXISTS(SELECT 1 FROM registro_lotes reg
 						 WHERE tipo_registro = 'organogramas' 
 						 		 AND reg.idIntegracao = MD5(CONCAT(organ.numero, organ.descricao, organ.tipoAdministracao, organ.configuracao)) 
 						 		 AND reg.id IS NOT NULL) """
	return sql