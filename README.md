# CFN-NukeEm

Python Utility to delete all CloudFormation stacks whose names begin with a common identifier, all at once!

Uses a [retry decorator](http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/) to handle Throttling exceptions.


Usage
-------------

```
python3 nuke_em.py --region <us-west-2> --identifier <user1-stacks>

```