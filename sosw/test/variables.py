TASKS_TABLE_CONFIG = {
    'row_mapper':       {
        'task_id':  'S',
        'labourer_id': 'S',
        'greenfield': 'N',
        'attempts':  'N',
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

TEST_CONFIG = {
    'init_clients':          [],
    'task_client_config':    {
        'init_clients':     [],
        'dynamo_db_config': TASKS_TABLE_CONFIG,
        'sosw_closed_tasks_table': 'autotest_sosw_closed_tasks'
    },
    'scavenger_client_config': {
        'init_clients':     [],
        'dynamo_db_config': TASKS_TABLE_CONFIG,
    },
    'ecology_client_config': {
        'test': True
    },
    'labourers':             {
            'some_function': {
                'arn': 'arn:aws:lambda:us-west-2:0000000000:function:some_function',
                'max_simultaneous_invocations': 10,
            }
    },
}
