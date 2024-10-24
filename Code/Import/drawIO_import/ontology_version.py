def get_rsm_topology_url(version: str = 'latest') -> str:
    start = 'http://cdm.ovh/rsm/topology/'
    if version == 'latest':
        return start + 'topology.ttl'
    else:
        return start + '/' + version + '/topology.ttl'
