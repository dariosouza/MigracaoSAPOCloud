
def sqlPrc():
    sql = f""" select 'ppas' as tipo_registro, 
                ppas.i_ppas as chave_dsk1,
                1 as sistema, 
                parametros_cloud.i_exercicios as anoInicial,
                parametros_cloud.recurso,
                parametros_cloud.funcional,
                parametros_cloud.organograma
            from (select i_exercicios,
                        max(if(chave = 'recurso', valor,'')) as recurso,
                        max(if(chave = 'funcional', valor,'')) as funcional,
                        max(if(chave = 'organograma', valor, '')) as organograma
                    from parametros_cloud 
                    where tipo = 'PPA'
                    group by i_exercicios) parametros_cloud 
                join ppas on ppas.i_exercicios = parametros_cloud.i_exercicios
            where parametros_cloud.i_exercicios <= 2022
            order by chave_dsk1 """
    return sql