from charms.reactive import when, when_not, set_state, is_state, remove_state
from charms.hadoop import get_hadoop_base
from jujubigdata.handlers import YARN
from jujubigdata import utils
from charmhelpers.core import hookenv


@when('hadoop.installed')
@when_not('resourcemanager.related')
def blocked():
    hookenv.status_set('blocked', 'Waiting for relation to ResourceManager')


@when('hadoop.installed', 'resourcemanager.related')
def set_spec(resourcemanager):
    hadoop = get_hadoop_base()
    resourcemanager.set_nodemanager_spec(hadoop.spec())


@when('resourcemanager.spec.mismatch')
def spec_mismatch(resourcemanager):
    hookenv.status_set('blocked',
                       'Spec mismatch with ResourceManager: {} != {}'.format(
                           resourcemanager.nodemanager_spec(), resourcemanager.resourcemanager_spec()))


@when('hadoop.installed', 'resourcemanager.related')
@when_not('resourcemanager.spec.mismatch', 'resourcemanager.ready', 'nodemanager.started')
def waiting(resourcemanager):
    hookenv.status_set('waiting', 'Waiting for ResourceManager')


@when('resourcemanager.ready')
@when_not('nodemanager.started')
def start_nodemanager(resourcemanager):
    hadoop = get_hadoop_base()
    yarn = YARN(hadoop)
    yarn.configure_nodemanager(resourcemanager.host(), resourcemanager.resourcemanager_port(), resourcemanager.hs_http(), resourcemanager.hs_ipc())
    #yarn.configure_nodemanager()
    utils.install_ssh_key('ubuntu', resourcemanager.ssh_key())
    yarn.start_nodemanager()
    resourcemanager.register()
    hadoop.open_ports('nodemanager')
    set_state('nodemanager.started')
    hookenv.status_set('active', 'Ready')


@when('nodemanager.started')
@when_not('resourcemanager.ready')
def stop_nodemanager():
    hadoop = get_hadoop_base()
    yarn = YARN(hadoop)
    yarn.stop_nodemanager()
    hadoop.close_ports('nodemanager')
    remove_state('nodemanager.started')
