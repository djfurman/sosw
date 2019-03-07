import boto3
import logging
import os
import random
import time
import unittest

from unittest.mock import Mock, MagicMock, patch


logging.getLogger('botocore').setLevel(logging.WARNING)

os.environ["STAGE"] = "test"
os.environ["autotest"] = "True"

from sosw.managers.task import TaskManager
from sosw.labourer import Labourer
from sosw.test.variables import TEST_CONFIG


class task_manager_UnitTestCase(unittest.TestCase):
    TEST_CONFIG = TEST_CONFIG['task_client_config']

    LABOURER = Labourer(id=1, arn='bar')


    def setUp(self):
        """
        We keep copies of main parameters here, because they may differ from test to test and cleanup needs them.
        This is responsibility of the test author to update these values if required from test.
        """

        self.patcher = patch("sosw.app.get_config")
        self.get_config_patch = self.patcher.start()

        self.config = self.TEST_CONFIG.copy()

        self.HASH_KEY = ('task_id', 'S')
        self.RANGE_KEY = ('labourer_id', 'S')
        self.table_name = self.config['dynamo_db_config']['table_name']

        self.manager = TaskManager(custom_config=self.config)
        self.manager.dynamo_db_client = MagicMock()
        self.manager.lambda_client = MagicMock()


    def tearDown(self):
        self.patcher.stop()


    def test_get_db_field_name(self):
        self.assertEqual(self.manager.get_db_field_name('task_id'), self.HASH_KEY[0], "Configured field name failed")
        self.assertEqual(self.manager.get_db_field_name('some_name'), 'some_name', "Default column name failed")


    def test_mark_task_invoked__calls_dynamo(self):
        self.manager.dynamo_db_client = MagicMock()
        self.manager.register_labourers([self.LABOURER])

        greenfield = round(time.time() - random.randint(0, 1000))
        delta = self.manager.config['greenfield_invocation_delta']

        task = {
            self.HASH_KEY[0]:  f"task_id_{self.LABOURER.id}_256",  # Task ID
            self.RANGE_KEY[0]: self.LABOURER.id,  # Worker ID
            'greenfield':      greenfield
        }

        # Do the actual tested job
        self.manager.mark_task_invoked(self.LABOURER, task)

        # Check the dynamo_client was called with correct payload to update
        self.manager.dynamo_db_client.update.assert_called_once()

        call_args, call_kwargs = self.manager.dynamo_db_client.update.call_args

        self.assertEqual(call_args[0],
                         {
                             self.HASH_KEY[0]: f"task_id_{self.LABOURER.id}_256", self.RANGE_KEY[0]: self.LABOURER.id
                         }), "The key of task is missing"
        self.assertEqual(call_kwargs['attributes_to_increment'], {'attempts': 1}), "Attempts counter not increased"

        gf = call_kwargs['attributes_to_update']['greenfield']
        self.assertEqual(round(gf, -2), round(time.time() + delta, -2)), "Greenfield was not updated"


    # @unittest.skip("This behavior is deprecated")
    # def test_mark_task_invoked__greenfield_counts_attempts(self):
    #     self.manager.dynamo_db_client = MagicMock()
    #
    #     greenfield = round(time.time() - random.randint(0, 1000))
    #     delta = self.manager.config['greenfield_invocation_delta']
    #
    #     task = {
    #         self.HASH_KEY[0]:  "task_id_42_256",  # Task ID
    #         self.RANGE_KEY[0]: 42,  # Worker ID
    #         'greenfield':      greenfield,
    #         'attempts':        3
    #     }
    #
    #     # Do the actual tested job
    #     self.manager.mark_task_invoked(task)
    #
    #     # Check the dynamo_client was called with correct payload to update
    #     self.manager.dynamo_db_client.update.assert_called_once()
    #
    #     call_args, call_kwargs = self.manager.dynamo_db_client.update.call_args
    #
    #     self.assertEqual(call_args[0],
    #                      {self.HASH_KEY[0]: "task_id_42_256", self.RANGE_KEY[0]: 42}), "The key of task is missing"
    #     self.assertEqual(call_kwargs['attributes_to_increment'], {'attempts': 1}), "Attempts counter not increased"
    #
    #     gf = call_kwargs['attributes_to_update']['greenfield']
    #     self.assertEqual(round(gf, -2), round(time.time() + delta * 4, -2),
    #                      "Greenfield was increased with respect to number of attempts")

    def test_invoke_task__validates_task(self):
        self.assertRaises(AttributeError, self.manager.invoke_task, labourer=self.LABOURER), "Missing task and task_id"
        self.assertRaises(AttributeError, self.manager.invoke_task, labourer=self.LABOURER, task_id='qwe',
                          task={1: 2}), "Both task and task_id."


    def test_invoke_task__calls__mark_task_invoked(self):
        self.manager.mark_task_invoked = MagicMock()

        self.manager.invoke_task(task_id='qwe', labourer=self.LABOURER)
        self.manager.mark_task_invoked.assert_called_once()


    def test_invoke_task__calls__get_task_by_id(self):
        self.manager.mark_task_invoked = MagicMock()
        self.manager.get_task_by_id = MagicMock()

        self.manager.invoke_task(task_id='qwe', labourer=self.LABOURER)
        self.manager.get_task_by_id.assert_called_once()


    def test_invoke_task__calls__lambda_client(self):
        self.manager.register_labourers([self.LABOURER])

        task = {
            self.HASH_KEY[0]:  f"task_id_{self.LABOURER.id}_256",  # Task ID
            self.RANGE_KEY[0]: self.LABOURER.id,  # Worker ID
            'payload':         {'foo': 23}
        }

        self.manager.get_task_by_id = MagicMock(return_value=task)

        self.manager.invoke_task(task_id=f'task_id_{self.LABOURER}_256', labourer=self.LABOURER)

        self.manager.lambda_client.invoke.assert_called_once()

        call_args, call_kwargs = self.manager.lambda_client.invoke.call_args

        self.assertEqual(call_kwargs['FunctionName'], self.LABOURER.arn)
        self.assertEqual(call_kwargs['Payload'], task['payload'])


    def test_invoke_task__not_calls__lambda_client_if_raised_conditional_exception(self):
        self.manager.register_labourers([self.LABOURER])

        task = {
            self.HASH_KEY[0]:  f"task_id_{self.LABOURER.id}_256",  # Task ID
            self.RANGE_KEY[0]: self.LABOURER.id,  # Worker ID
            'payload':         {'foo': 23}
        }


        class ConditionalCheckFailedException(Exception):
            pass


        self.manager.get_task_by_id = MagicMock(return_value=task)
        self.manager.mark_task_invoked = MagicMock()
        self.manager.mark_task_invoked.side_effect = ConditionalCheckFailedException("Boom")

        self.manager.invoke_task(task_id=f'task_id_{self.LABOURER}_256', labourer=self.LABOURER)

        self.manager.lambda_client.invoke.assert_not_called()
        self.assertEqual(self.manager.stats['concurrent_task_invocations_skipped'], 1)


    def test_register_labourers(self):
        lab = Labourer(id=42)

        with patch('time.time') as t:
            t.return_value = 123

            self.manager.register_labourers(labourers=[lab])

        invoke_time = 123 + self.manager.config['greenfield_invocation_delta']

        self.assertEqual(lab.get_timestamp('start'), 123)
        self.assertEqual(lab.get_timestamp('invoked'), invoke_time)
        self.assertEqual(lab.get_timestamp('expired'), invoke_time - lab.duration - lab.cooldown)


    def test_calculate_count_of_running_tasks_for_labourer(self):
        lab = Labourer(id=42)
        self.manager.get_running_tasks_for_labourer = MagicMock(return_value=[1, 2, 3])

        self.assertEqual(self.manager.calculate_count_of_running_tasks_for_labourer(labourer=lab), 3)
        self.manager.get_running_tasks_for_labourer.assert_called_once()


    def test_get_labourers(self):
        self.config['labourers'] = {
            'some_lambda': {'foo': 'bar', 'arn': '123'},
            'some_lambda2': {'foo': 'baz'},
        }
        self.task_client = TaskManager(custom_config=self.config)

        result = self.task_client.get_labourers()
        self.assertEqual(len(result), 2)
        self.assertEqual(result['some_lambda'].foo, 'bar')
        self.assertEqual(result['some_lambda'].arn, '123')
        self.assertEqual(result['some_lambda2'].foo, 'baz')


    def test_archive_task(self):
        task_id = '918273'
        task = {'labourer_id': 'some_lambda', 'task_id': task_id, 'payload': '{}', 'completed_at': '1551962375',
                'closed_at': '111'}

        # Mock
        self.manager.dynamo_db_client = MagicMock()
        self.manager.get_task_by_id = Mock(return_value=task)

        # Call
        self.manager.archive_task(task_id)

        # Check calls
        expected_completed_task = task.copy()
        expected_completed_task['labourer_id_task_status'] = 'some_lambda_1'
        self.manager.dynamo_db_client.put.assert_called_once_with(expected_completed_task, table_name=self.TEST_CONFIG['sosw_closed_tasks_table'])
        self.manager.dynamo_db_client.delete.assert_called_once_with({'labourer_id': 'some_lambda', 'task_id': task_id})
