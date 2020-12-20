import boto3
import argparse
import time
from functools import wraps
from pprint import pprint
from botocore.exceptions import ClientError

def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.
    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry  # true decorator
    return deco_retry

class NukeEm():

    def __init__(self):
        self.client = None

    def initialize(self, region):
        self.client = boto3.client('cloudformation', region_name=region)
        
    def find_stacks(self, next_token=None):
        ''' lists all cloudformation stacks '''
        results = []
        response = None
        if next_token:
            response = self.client.list_stacks(
                NextToken=next_token,
                StackStatusFilter=[
                'CREATE_FAILED','CREATE_COMPLETE','ROLLBACK_FAILED','ROLLBACK_COMPLETE','DELETE_FAILED','UPDATE_COMPLETE','UPDATE_ROLLBACK_FAILED','UPDATE_ROLLBACK_COMPLETE'
                ]
            )
        else:
            response = self.client.list_stacks(
                StackStatusFilter=[
                'CREATE_FAILED','CREATE_COMPLETE','ROLLBACK_FAILED','ROLLBACK_COMPLETE','DELETE_FAILED','UPDATE_COMPLETE','UPDATE_ROLLBACK_FAILED','UPDATE_ROLLBACK_COMPLETE'
                ]
            )
        results.append(
            [stack['StackName'] for stack in response['StackSummaries']]
        )
        if response.get('NextToken') is not None:
            results.append(self.find_stacks(response['NextToken']))
        stack_list = [item for sublist in results for item in sublist]
        return stack_list


    def filter_stacks(self, identifier, list):
        '''filter stacks with identifier'''
        result = [i for i in list if i.startswith(identifier)]
        return result


    @retry(ClientError, tries=4)
    def delete_stack(self, stack):
        ''' delete stack with retry'''
        response = self.client.delete_stack(
            StackName=stack
        )


    def clean_env(self, stack_list):
        ''' delete filtered stack list'''
        for stack in stack_list:
            self.delete_stack(stack)


    def cfn_nuke(self, identifier):
        stacks = self.find_stacks()
        filtered_stack_list = self.filter_stacks(identifier, stacks)
        print("Deleting the following stacks....")
        pprint(filtered_stack_list)
        self.clean_env(filtered_stack_list)


def main():
    parser = argparse.ArgumentParser(description='Clean Dev Envs')
    parser.add_argument('--region', help='region', required=True)
    parser.add_argument('--identifier', help='example: development-stacks', required=True)
    args = parser.parse_args()
    env_cleaner = NukeEm()
    env_cleaner.initialize(args.region)
    env_cleaner.cfn_nuke(args.identifier)
    print("Deletion triggered for all stacks")

if __name__ == "__main__":
    main()