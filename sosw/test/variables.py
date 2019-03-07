TASKS_TABLE_CONFIG = {
    'row_mapper':       {
        'task_id':     'S',
        'labourer_id': 'S',
        'greenfield':  'N',
        'attempts':    'N',
    },
    'required_fields':  ['task_id', 'labourer_id'],
    'table_name':       'autotest_sosw_tasks',
    'index_greenfield': 'autotest_sosw_tasks_greenfield',
    'field_names':      {
        'task_id':     'task_id',
        'labourer_id': 'labourer_id',
        'greenfield':  'greenfield',
    }
}

TEST_ECOLOGY_CLIENT_CONFIG = {
    'test': True
}

TEST_TASK_CLIENT_CONFIG = {
    'init_clients':          [],
    'dynamo_db_config':      TASKS_TABLE_CONFIG,
    'ecology_client_config': TEST_ECOLOGY_CLIENT_CONFIG,
    'labourers':             {
        'some_function': {
            'arn':                          'arn:aws:lambda:us-west-2:0000000000:function:some_function',
            'max_simultaneous_invocations': 10,
        },
        1: {'arn': 'bar'},
    },
}

TEST_ORCHESTRATOR_CONFIG = {
    'init_clients':          [],
    'task_client_config':    TEST_TASK_CLIENT_CONFIG,
    'ecology_client_config': TEST_ECOLOGY_CLIENT_CONFIG,
}

TEST_SCAVENGER_CONFIG = {
    'init_clients':     [],
    'dynamo_db_config': TASKS_TABLE_CONFIG,
}

TEST_SCHEDULER_CONFIG = {
    'init_clients':       [],
    'task_client_config': TEST_TASK_CLIENT_CONFIG,
}
