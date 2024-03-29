import boto3
import botocore
import click

session = boto3.Session(profile_name='shotty')
ec2 = session.resource('ec2')

def filter_instances(project):
    instances = []
    if project:
        filters=[{'Name':'tag:Project','Values':[project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances=  ec2.instances.all()
    return instances

@click.group()
def cli():
    """ Add both groups"""

@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""
@snapshots.command('list')
@click.option('--project',default=None,
    help="Only snapshots for project (tag Project:<name>)")
def list_snapshots(project):
    "List EC2 Snapshots"
    instances = filter_instances(project)
    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(",".join((
                    s.id,
                    v.id,
                    i.id,
                    s.state,
                    s.progress,
                    s.start_time.strftime("%c")
                )))
    return



@cli.group('volumes')
def volumes():
    """Commands for volumes"""
@volumes.command('list')
@click.option('--project',default=None,
    help="Only volumes for project (tag Project:<name>)")
def list_volumes(project):
    "List EC2 Volumes"
    instances = filter_instances(project)
    for i in instances:
        for v in i.volumes.all():
            print(",".join((
                v.id,
                i.id,
                v.state,
                str(v.size) + "GiB",
                v.encrypted and "Encrypted" or "Not Encrypted"
            )))
    return

@cli.group('instances')
def instances():
    """Commands for instances"""
@instances.command('list')
@click.option('--project',default=None,
    help="Only instances for project (tag Project:<name>)")
def list_instances(project):
    "List EC2 Instances"
    instances = filter_instances(project)
    for i in instances:
        tags = {t['Key']: t['Value'] for t in i.tags or [] }
        print(', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('Project','<no project>')
        )))
    return

@instances.command('snapshot',help="Create snapshots of all volumes")
@click.option('--project',default=None,
    help="Only instances for project (tag Project:<name>)")
def create_snapshots(project):
    "Create snapshots for EC2 Instances"
    instances = filter_instances(project)
    for i in instances:
        #Print("Stopping..{0}".format(i.id))
        i.stop()
        i.wait_until_stopped()
        for v in i.volumes.all():
            print("Create Snapshot of {0}".format(v.id))
            v.create_snapshot(Description="Snapshot for SnapshotAlyzer 30000")
        #Print("ReStarting..{0}".format(i.id))
        i.start()
        i.wait_until_running()
    print("Job Done!")
    return


@instances.command('stop')
@click.option('--project',default=None,
    help="Stopping instances")
def stop_instances(project):
    "Stop EC2 Instances"
    instances = filter_instances(project)
    for i in instances:
        print("Stopping {0}... ".format(i.id))
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print("Could not stop {0}. ".format(i.id)+str(e))
            continue
    return

@instances.command('start')
@click.option('--project',default=None,
    help="Starting instances")
def start_instances(project):
    "Start EC2 Instances"
    instances = filter_instances(project)
    for i in instances:
        print("Starting {0}... ".format(i.id))
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print("Could not start {0}. ".format(i.id)+str(e))
            continue
    return


if __name__ == '__main__':
    #print(sys.argv)
    cli()
