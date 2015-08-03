import click
import sys
import time

from solar.core import actions
from solar.core import resource
from solar.core import signals
from solar.core import validation
from solar.core.resource import virtual_resource as vr
from solar import errors

from solar.interfaces.db import get_db


GIT_PUPPET_LIBS_URL = 'https://github.com/CGenie/puppet-libs-resource'


# TODO
# Resource for repository OR puppet apt-module in run.pp
# add-apt-repository cloud-archive:juno
# To discuss: install stuff in Docker container

# NOTE
# No copy of manifests, pull from upstream (implemented in the puppet handler)
# Official puppet manifests, not fuel-library


@click.group()
def main():
    pass


@click.command()
def deploy():
    db = get_db()
    db.clear()

    signals.Connections.clear()

    node1, node2 = vr.create('nodes', 'templates/nodes.yml', {})
    
    # MARIADB
    mariadb_service1 = vr.create('mariadb_service1', 'resources/mariadb_service', {
        'image': 'mariadb',
        'port': 3306
    })[0]

    signals.connect(node1, mariadb_service1)

    # RABBIT
    rabbitmq_service1 = vr.create('rabbitmq_service1', 'resources/rabbitmq_service/', {
        'management_port': 15672,
        'port': 5672,
    })[0]
    openstack_vhost = vr.create('openstack_vhost', 'resources/rabbitmq_vhost/', {
        'vhost_name': 'openstack'
    })[0]

    openstack_rabbitmq_user = vr.create('openstack_rabbitmq_user', 'resources/rabbitmq_user/', {
        'user_name': 'openstack',
        'password': 'openstack_password'
    })[0]

    signals.connect(node1, rabbitmq_service1)
    signals.connect(rabbitmq_service1, openstack_vhost)
    signals.connect(rabbitmq_service1, openstack_rabbitmq_user)
    signals.connect(openstack_vhost, openstack_rabbitmq_user, {
        'vhost_name',
    })

    # KEYSTONE
    keystone_puppet = vr.create('keystone_puppet', 'resources/keystone_puppet', {})[0]
    keystone_db = vr.create('keystone_db', 'resources/mariadb_db/', {
        'db_name': 'keystone_db',
        'login_user': 'root'
    })[0]
    keystone_db_user = vr.create('keystone_db_user', 'resources/mariadb_user/', {
        'user_name': 'keystone',
        'user_password': 'keystone',
    })[0]
    keystone_service_endpoint = vr.create('keystone_service_endpoint', 'resources/keystone_service_endpoint', {
        'endpoint_name': 'keystone',
        'adminurl': 'http://{{admin_ip}}:{{admin_port}}/v2.0',
        'internalurl': 'http://{{internal_ip}}:{{internal_port}}/v2.0',
        'publicurl': 'http://{{public_ip}}:{{public_port}}/v2.0',
        'description': 'OpenStack Identity Service',
        'type': 'identity'
    })[0]

    admin_tenant = vr.create('admin_tenant', 'resources/keystone_tenant', {
        'tenant_name': 'admin'
    })[0]
    admin_user = vr.create('admin_user', 'resources/keystone_user', {
        'user_name': 'admin',
        'user_password': 'admin'
    })[0]
    admin_role = vr.create('admin_role', 'resources/keystone_role', {
        'role_name': 'admin'
    })[0]
    services_tenant = vr.create('services_tenant', 'resources/keystone_tenant', {
        'tenant_name': 'services'
    })[0]

    signals.connect(node1, keystone_db)
    signals.connect(node1, keystone_db_user)
    signals.connect(node1, keystone_puppet)
    signals.connect(mariadb_service1, keystone_db, {
        'port': 'login_port',
        'root_user': 'login_user',
        'root_password': 'login_password',
        'ip' : 'db_host',
    })
    signals.connect(keystone_db, keystone_db_user, {
        'db_name',
        'login_port',
        'login_user',
        'login_password',
        'db_host'
    })

    signals.connect(node1, keystone_service_endpoint)
    signals.connect(keystone_puppet, keystone_service_endpoint, {
        'admin_token': 'admin_token',
        'admin_port': ['admin_port', 'keystone_admin_port'],
        'ip': ['keystone_host', 'admin_ip', 'internal_ip', 'public_ip'],
        'port': ['internal_port', 'public_port'],
    })

    signals.connect(keystone_puppet, admin_tenant)
    signals.connect(keystone_puppet, admin_tenant, {
        'admin_port': 'keystone_port',
        'ip': 'keystone_host'
    })
    signals.connect(admin_tenant, admin_user)
    signals.connect(admin_user, admin_role)

    signals.connect(keystone_puppet, services_tenant)
    signals.connect(keystone_puppet, services_tenant, {
        'admin_port': 'keystone_port',
        'ip': 'keystone_host'
    })

    signals.connect(keystone_db, keystone_puppet, {
        'db_name',
    })
    signals.connect(keystone_db_user, keystone_puppet, {
        'user_name': 'db_user',
        'user_password': 'db_password',
        'db_host' : 'db_host'
    })

    # OPENRC
    openrc = vr.create('openrc_file', 'resources/openrc_file', {})[0]

    signals.connect(node1, openrc)
    signals.connect(keystone_puppet, openrc, {'ip': 'keystone_host', 'admin_port':'keystone_port'})
    signals.connect(admin_user, openrc, {'user_name': 'user_name','user_password':'password', 'tenant_name': 'tenant'})

    # NEUTRON
    # TODO: vhost cannot be specified in neutron Puppet manifests so this user has to be admin anyways
    neutron_puppet = vr.create('neutron_puppet', 'resources/neutron_puppet', {})[0]

    neutron_keystone_user = vr.create('neutron_keystone_user', 'resources/keystone_user', {
        'user_name': 'neutron',
        'user_password': 'neutron'
    })[0]
    neutron_keystone_role = vr.create('neutron_keystone_role', 'resources/keystone_role', {
        'role_name': 'admin'
    })[0]
    neutron_keystone_service_endpoint = vr.create('neutron_keystone_service_endpoint', 'resources/keystone_service_endpoint', {
        'endpoint_name': 'neutron',
        'adminurl': 'http://{{admin_ip}}:{{admin_port}}',
        'internalurl': 'http://{{internal_ip}}:{{internal_port}}',
        'publicurl': 'http://{{public_ip}}:{{public_port}}',
        'description': 'OpenStack Network Service',
        'type': 'network'
    })[0]

    signals.connect(node1, neutron_puppet)
    signals.connect(rabbitmq_service1, neutron_puppet, {
        'ip': 'rabbitmq_host',
        'port': 'rabbitmq_port'
    })
    signals.connect(openstack_rabbitmq_user, neutron_puppet, {
        'user_name': 'rabbitmq_user',
        'password': 'rabbitmq_password'})
    signals.connect(openstack_vhost, neutron_puppet, {
        'vhost_name': 'rabbitmq_virtual_host'})
    signals.connect(admin_user, neutron_puppet, {
        'user_name': 'keystone_user',
        'user_password': 'keystone_password',
        'tenant_name': 'keystone_tenant'
    })
    signals.connect(keystone_puppet, neutron_puppet, {
        'ip': 'keystone_host',
        'port': 'keystone_port'
    })
    signals.connect(services_tenant, neutron_keystone_user)
    signals.connect(neutron_keystone_user, neutron_keystone_role)
    signals.connect(keystone_puppet, neutron_keystone_service_endpoint, {
        'ip': ['ip', 'keystone_host'],
        'ssh_key': 'ssh_key',
        'ssh_user': 'ssh_user',
        'admin_port': 'keystone_admin_port',
        'admin_token': 'admin_token',
    })
    signals.connect(neutron_puppet, neutron_keystone_service_endpoint, {
        'ip': ['admin_ip', 'internal_ip', 'public_ip'],
        'port': ['admin_port', 'internal_port', 'public_port'],
    })

    # CINDER
    cinder_puppet = vr.create('cinder_puppet', 'resources/cinder_puppet', {})[0]
    cinder_db = vr.create('cinder_db', 'resources/mariadb_db/', {
        'db_name': 'cinder_db', 'login_user': 'root'})[0]
    cinder_db_user = vr.create('cinder_db_user', 'resources/mariadb_user/', {
        'user_name': 'cinder', 'user_password': 'cinder', 'login_user': 'root'})[0]
    cinder_keystone_user = vr.create('cinder_keystone_user', 'resources/keystone_user', {
        'user_name': 'cinder', 'user_password': 'cinder'})[0]
    cinder_keystone_role = vr.create('cinder_keystone_role', 'resources/keystone_role', {
        'role_name': 'admin'})[0]
    cinder_keystone_service_endpoint = vr.create(
        'cinder_keystone_service_endpoint',
        'resources/keystone_service_endpoint', {
            'endpoint_name': 'cinder',
            'adminurl': 'http://{{admin_ip}}:{{admin_port}}/v2/%(tenant_id)s',
            'internalurl': 'http://{{internal_ip}}:{{internal_port}}/v2/%(tenant_id)s',
            'publicurl': 'http://{{public_ip}}:{{public_port}}/v2/%(tenant_id)s',
            'description': 'OpenStack Block Storage Service', 'type': 'volume'})[0]

    signals.connect(node1, cinder_puppet)
    signals.connect(node1, cinder_db)
    signals.connect(node1, cinder_db_user)
    signals.connect(rabbitmq_service1, cinder_puppet, {'ip': 'rabbit_host', 'port': 'rabbit_port'})
    signals.connect(admin_user, cinder_puppet, {'user_name': 'keystone_user', 'user_password': 'keystone_password', 'tenant_name': 'keystone_tenant'}) #?
    signals.connect(openstack_vhost, cinder_puppet, {'vhost_name': 'rabbit_virtual_host'})
    signals.connect(openstack_rabbitmq_user, cinder_puppet, {'user_name': 'rabbit_userid', 'password': 'rabbit_password'})
    signals.connect(mariadb_service1, cinder_db, {
        'port': 'login_port',
        'root_password': 'login_password',
        'root_user': 'login_user',
        'ip' : 'db_host'})
    signals.connect(mariadb_service1, cinder_db_user, {'port': 'login_port', 'root_password': 'login_password'})
    signals.connect(cinder_db, cinder_db_user, {'db_name', 'db_host'})
    signals.connect(cinder_db_user, cinder_puppet, {
        'user_name':'db_user',
        'db_name':'db_name',
        'user_password':'db_password',
        'db_host' : 'db_host'})
    signals.connect(keystone_puppet, cinder_puppet, {'ip': 'keystone_host', 'admin_port': 'keystone_port'}) #or non admin port?
    signals.connect(services_tenant, cinder_keystone_user)
    signals.connect(cinder_keystone_user, cinder_keystone_role)
    signals.connect(cinder_keystone_user, cinder_puppet, {'user_name': 'keystone_user', 'tenant_name': 'keystone_tenant', 'user_password': 'keystone_password'})
    signals.connect(mariadb_service1, cinder_puppet, {'ip':'ip'})
    signals.connect(cinder_puppet, cinder_keystone_service_endpoint, {
        'ssh_key': 'ssh_key', 'ssh_user': 'ssh_user',
        'ip': ['ip', 'keystone_host', 'admin_ip', 'internal_ip', 'public_ip'],
        'port': ['admin_port', 'internal_port', 'public_port'],})
    signals.connect(keystone_puppet, cinder_keystone_service_endpoint, {
        'admin_port': 'keystone_admin_port', 'admin_token': 'admin_token'})
    
    # CINDER API
    cinder_api_puppet = vr.create('cinder_api_puppet', 'resources/cinder_api_puppet', {})[0]
    signals.connect(node1, cinder_api_puppet)
    signals.connect(cinder_puppet, cinder_api_puppet, {
        'keystone_password', 'keystone_tenant', 'keystone_user'})
    signals.connect(cinder_puppet, cinder_api_puppet, {
        'keystone_host': 'keystone_auth_host',
        'keystone_port': 'keystone_auth_port'})

    # CINDER SCHEDULER
    cinder_scheduler_puppet = vr.create('cinder_scheduler_puppet', 'resources/cinder_scheduler_puppet', {})[0]
    signals.connect(node1, cinder_scheduler_puppet)
    signals.connect(cinder_puppet, cinder_scheduler_puppet)

    # CINDER VOLUME
    cinder_volume_puppet = vr.create('cinder_volume_puppet', 'resources/cinder_volume_puppet', {})[0]
    signals.connect(node1, cinder_volume_puppet)
    signals.connect(cinder_puppet, cinder_volume_puppet)
    
    # NOVA
    nova_puppet = vr.create('nova_puppet', 'resources/nova_puppet', {})[0]
    nova_db = vr.create('nova_db', 'resources/mariadb_db/', {
        'db_name': 'nova_db',
        'login_user': 'root'})[0]
    nova_db_user = vr.create('nova_db_user', 'resources/mariadb_user/', {
        'user_name': 'nova',
        'user_password': 'nova',
        'login_user': 'root'})[0]
    nova_keystone_user = vr.create('nova_keystone_user', 'resources/keystone_user', {
        'user_name': 'nova',
        'user_password': 'nova'})[0]
    nova_keystone_role = vr.create('nova_keystone_role', 'resources/keystone_role', {
        'role_name': 'admin'})[0]
    nova_keystone_service_endpoint = vr.create('nova_keystone_service_endpoint', 'resources/keystone_service_endpoint', {
        'endpoint_name': 'nova',
        'adminurl': 'http://{{admin_ip}}:{{admin_port}}/v2/%(tenant_id)s',
        'internalurl': 'http://{{internal_ip}}:{{internal_port}}/v2/%(tenant_id)s',
        'publicurl': 'http://{{public_ip}}:{{public_port}}/v2/%(tenant_id)s',
        'description': 'OpenStack Compute Service',
        'type': 'compute'})[0]

    signals.connect(node1, nova_puppet)
    signals.connect(node1, nova_db)
    signals.connect(node1, nova_db_user)
    signals.connect(mariadb_service1, nova_db, {
        'port': 'login_port',
        'root_password': 'login_password',
        'root_user': 'login_user',
        'ip' : 'db_host'})
    signals.connect(mariadb_service1, nova_db_user, {
        'port': 'login_port',
        'root_password': 'login_password'})
    signals.connect(admin_user, nova_puppet, {'user_name': 'keystone_user', 'user_password': 'keystone_password', 'tenant_name': 'keystone_tenant'}) #?
    signals.connect(openstack_vhost, nova_puppet, {'vhost_name': 'rabbit_virtual_host'})
    signals.connect(nova_db, nova_db_user, {'db_name', 'db_host'})
    signals.connect(services_tenant, nova_keystone_user)
    signals.connect(nova_keystone_user, nova_keystone_role)
    signals.connect(keystone_puppet, nova_puppet, {
        'ip': 'keystone_host',
        'admin_port': 'keystone_port'})
    signals.connect(nova_keystone_user, nova_puppet, {
        'user_name': 'keystone_user',
        'tenant_name': 'keystone_tenant',
        'user_password': 'keystone_password'})
    signals.connect(rabbitmq_service1, nova_puppet, {
        'ip': 'rabbit_host', 'port': 'rabbit_port'})
    signals.connect(openstack_rabbitmq_user, nova_puppet, {
        'user_name': 'rabbit_userid',
        'password': 'rabbit_password'})
    signals.connect(keystone_puppet, nova_keystone_service_endpoint, {
        'ip': 'keystone_host',
        'admin_port': 'keystone_admin_port',
        'admin_token': 'admin_token'})
    signals.connect(mariadb_service1, nova_puppet, {
        'ip':'db_host'})
    signals.connect(nova_db_user, nova_puppet, {
        'user_name':'db_user',
        'db_name':'db_name',
        'user_password':'db_password',
        'db_host' : 'db_host'})
    signals.connect(nova_puppet, nova_keystone_service_endpoint, {
        'ip': ['ip', 'keystone_host', 'public_ip', 'internal_ip', 'admin_ip'],
        'port': ['admin_port', 'internal_port', 'public_port'],
        'ssh_key': 'ssh_key',
        'ssh_user': 'ssh_user'})

    # NOVA API
    nova_api_puppet = vr.create('nova_api_puppet', 'resources/nova_api_puppet', {})[0]
    signals.connect(node1, nova_api_puppet)
    signals.connect(nova_puppet, nova_api_puppet, {
        'keystone_tenant': 'admin_tenant_name',
        'keystone_user': 'admin_user',
        'keystone_password': 'admin_password',
        'keystone_host': 'auth_host',
        'keystone_port': 'auth_port'})

    # NOVA CONDUCTOR
    nova_conductor_puppet = vr.create('nova_conductor_puppet', 'resources/nova_conductor_puppet', {})[0]
    signals.connect(node1, nova_conductor_puppet)
    signals.connect(nova_puppet, nova_conductor_puppet)

    # NOVA COMPUTE
    # Deploy chain (nova, node_networking(TODO)) -> (nova_compute_libvirt, nova_neutron) -> nova_compute
    nova_compute_puppet = vr.create('nova_compute_puppet', 'resources/nova_compute_puppet', {})[0]
    nova_puppet2 = vr.create('nova_puppet2', 'resources/nova_puppet', {})[0]
    signals.connect(nova_puppet, nova_puppet2, {
        'ensure_package', 'rabbit_host',
        'rabbit_password', 'rabbit_port', 'rabbit_userid',
        'rabbit_virtual_host', 'db_user', 'db_password',
        'db_name', 'db_host', 'keystone_password',
        'keystone_port', 'keystone_host', 'keystone_tenant',
        'keystone_user',
    })
    # TODO(bogdando): Make a connection for nova_puppet2.glance_api_servers = "glance_api_puppet.ip:glance_api_puppet.bind_port"
    signals.connect(node2, nova_puppet2)
    signals.connect(node2, nova_compute_puppet)

    # NOVA COMPUTE LIBVIRT, NOVA_NEUTRON
    # NOTE(bogdando): changes nova config, so should notify nova compute service
    nova_compute_libvirt_puppet = vr.create('nova_compute_libvirt_puppet', 'resources/nova_compute_libvirt_puppet', {})[0]
    signals.connect(node2, nova_compute_libvirt_puppet)
    nova_neutron_puppet = vr.create('nova_neutron_puppet', 'resources/nova_neutron_puppet', {})[0]
    signals.connect(node2, nova_neutron_puppet)

    # signals.connect(keystone_puppet, nova_network_puppet, {'ip': 'keystone_host', 'port': 'keystone_port'})
    # signals.connect(keystone_puppet, nova_keystone_service_endpoint, {'ip': 'keystone_host', 'admin_port': 'keystone_port', 'admin_token': 'admin_token'})
    # signals.connect(rabbitmq_service1, nova_network_puppet, {'ip': 'rabbitmq_host', 'port': 'rabbitmq_port'})

    # GLANCE (base and API)
    glance_api_puppet = vr.create('glance_api_puppet', 'resources/glance_puppet', {})[0]
    glance_db_user = vr.create('glance_db_user', 'resources/mariadb_user/', {
        'user_name': 'glance', 'user_password': 'glance', 'login_user': 'root'})[0]
    glance_db = vr.create('glance_db', 'resources/mariadb_db/', {
        'db_name': 'glance', 'login_user': 'root'})[0]
    glance_keystone_user = vr.create('glance_keystone_user', 'resources/keystone_user', {
        'user_name': 'glance', 'user_password': 'glance123'})[0]
    glance_keystone_role = vr.create('glance_keystone_role', 'resources/keystone_role', {
        'role_name': 'admin'})[0]
    glance_keystone_service_endpoint = vr.create(
        'glance_keystone_service_endpoint',
        'resources/keystone_service_endpoint', {
            'endpoint_name': 'glance',
            'adminurl': 'http://{{admin_ip}}:{{admin_port}}',
            'internalurl': 'http://{{internal_ip}}:{{internal_port}}',
            'publicurl': 'http://{{public_ip}}:{{public_port}}',
            'description': 'OpenStack Image Service', 'type': 'volume'})[0]

    signals.connect(node1, glance_api_puppet)
    signals.connect(node1, glance_db)
    signals.connect(node1, glance_db_user)
    signals.connect(admin_user, glance_api_puppet, {
        'user_name': 'keystone_user', 'user_password': 'keystone_password',
        'tenant_name': 'keystone_tenant'}) #?
    signals.connect(mariadb_service1, glance_db, {
        'port': 'login_port',
        'root_password': 'login_password',
        'root_user': 'login_user',
        'ip' : 'db_host'})
    signals.connect(mariadb_service1, glance_db_user, {'port': 'login_port', 'root_password': 'login_password'})
    signals.connect(glance_db, glance_db_user, {'db_name', 'db_host'})
    signals.connect(glance_db_user, glance_api_puppet, {
        'user_name':'db_user',
        'db_name':'db_name',
        'user_password':'db_password',
        'db_host' : 'db_host'})
    signals.connect(keystone_puppet, glance_api_puppet, {'ip': 'keystone_host', 'admin_port': 'keystone_port'}) #or non admin port?
    signals.connect(services_tenant, glance_keystone_user)
    signals.connect(glance_keystone_user, glance_keystone_role)
    signals.connect(glance_keystone_user, glance_api_puppet, {
        'user_name': 'keystone_user', 'tenant_name': 'keystone_tenant',
        'user_password': 'keystone_password'})
    signals.connect(mariadb_service1, glance_api_puppet, {'ip':'ip'})
    signals.connect(glance_api_puppet, glance_keystone_service_endpoint, {
        'ssh_key': 'ssh_key', 'ssh_user': 'ssh_user',
        'ip': ['ip', 'keystone_host', 'admin_ip', 'internal_ip', 'public_ip'],
        'bind_port': ['admin_port', 'internal_port', 'public_port'],})
    signals.connect(keystone_puppet, glance_keystone_service_endpoint, {
        'admin_port': 'keystone_admin_port', 'admin_token': 'admin_token'})

    # GLANCE REGISTRY
    glance_registry_puppet = vr.create('glance_registry_puppet', 'resources/glance_registry_puppet', {})[0]
    signals.connect(node1, glance_registry_puppet)
    signals.connect(glance_api_puppet, glance_registry_puppet)
    # API and registry should not listen same ports
    # should not use the same log destination and a pipeline,
    # so disconnect them and restore the defaults
    signals.disconnect_receiver_by_input(glance_registry_puppet, 'bind_port')
    signals.disconnect_receiver_by_input(glance_registry_puppet, 'log_file')
    signals.disconnect_receiver_by_input(glance_registry_puppet, 'pipeline')
    glance_registry_puppet.update({
        'bind_port': 9191,
        'log_file': '/var/log/glance/registry.log',
        'pipeline': 'keystone',
    })

    has_errors = False
    for r in locals().values():
        if not isinstance(r, resource.Resource):
            continue

        print 'Validating {}'.format(r.name)
        errors = validation.validate_resource(r)
        if errors:
            has_errors = True
            print 'ERROR: %s: %s' % (r.name, errors)

    if has_errors:
        sys.exit(1)


    # run
    actions.resource_action(rabbitmq_service1, 'run')
    actions.resource_action(openstack_vhost, 'run')
    actions.resource_action(openstack_rabbitmq_user, 'run')

    actions.resource_action(mariadb_service1, 'run')

    actions.resource_action(keystone_db, 'run')
    actions.resource_action(keystone_db_user, 'run')
    actions.resource_action(keystone_puppet, 'run')
    actions.resource_action(openrc, 'run')

    actions.resource_action(admin_tenant, 'run')
    actions.resource_action(admin_user, 'run')
    actions.resource_action(admin_role, 'run')

    actions.resource_action(keystone_service_endpoint, 'run')
    actions.resource_action(services_tenant, 'run')

    actions.resource_action(neutron_keystone_user, 'run')
    actions.resource_action(neutron_keystone_role, 'run')
    actions.resource_action(neutron_puppet, 'run')
    actions.resource_action(neutron_keystone_service_endpoint, 'run')

    actions.resource_action(cinder_db, 'run')
    actions.resource_action(cinder_db_user, 'run')
    actions.resource_action(cinder_keystone_user, 'run')
    actions.resource_action(cinder_keystone_role, 'run')
    actions.resource_action(cinder_puppet, 'run')
    actions.resource_action(cinder_keystone_service_endpoint, 'run')
    actions.resource_action(cinder_api_puppet, 'run')
    actions.resource_action(cinder_scheduler_puppet, 'run')
    actions.resource_action(cinder_volume_puppet, 'run')
    
    actions.resource_action(nova_db, 'run')
    actions.resource_action(nova_db_user, 'run')
    actions.resource_action(nova_keystone_user, 'run')
    actions.resource_action(nova_keystone_role, 'run')
    actions.resource_action(nova_puppet, 'run')
    actions.resource_action(nova_keystone_service_endpoint, 'run')
    actions.resource_action(nova_api_puppet, 'run')
    actions.resource_action(nova_conductor_puppet, 'run')

    actions.resource_action(nova_puppet2, 'run')
    actions.resource_action(nova_compute_libvirt_puppet, 'run')
    actions.resource_action(nova_neutron_puppet, 'run')
    actions.resource_action(nova_compute_puppet, 'run')

    actions.resource_action(glance_db, 'run')
    actions.resource_action(glance_db_user, 'run')
    actions.resource_action(glance_keystone_user, 'run')
    actions.resource_action(glance_keystone_role, 'run')  
    actions.resource_action(glance_keystone_service_endpoint, 'run')
    actions.resource_action(glance_api_puppet, 'run')
    actions.resource_action(glance_registry_puppet, 'run')

    time.sleep(10)


@click.command()
def undeploy():
    db = get_db()

    to_remove = [
        'glance_registry_puppet',
        'glance_api_puppet',
        'glance_keystone_service_endpoint',
        'glance_keystone_role',
        'glance_keystone_user',
        'glance_db_user',
        'glance_db',
        'nova_db',
        'nova_db_user',
        'nova_keystone_service_endpoint',
        'nova_conductor_puppet',
        'nova_api_puppet',
        'nova_puppet',
        'nova_compute_puppet',
        'nova_neutron_puppet',
        'nova_compute_libvirt_puppet',
        'nova_puppet2',
        'cinder_volume_puppet',
        'cinder_scheduler_puppet',
        'cinder_api_puppet',
        'cinder_keystone_service_endpoint',
        'cinder_puppet',
        'cinder_keystone_role',
        'cinder_keystone_user',
        'cinder_db_user',
        'cinder_db',
        'neutron_keystone_service_endpoint',
        'neutron_puppet',
        'neutron_keystone_role',
        'neutron_keystone_user',
        'services_tenant',
        'keystone_service_endpoint',
        'admin_role',
        'admin_user',
        'admin_tenant',
        'openrc_file',
        'keystone_puppet',
        'keystone_db_user',
        'keystone_db',
        'mariadb_service1',
        'openstack_rabbitmq_user',
        'openstack_vhost',
        'rabbitmq_service1',
    ]

    resources = map(resource.wrap_resource, db.get_list(collection=db.COLLECTIONS.resource))
    resources = {r.name: r for r in resources}

    for name in to_remove:
        try:
            actions.resource_action(resources[name], 'remove')
        except errors.SolarError as e:
            print 'WARNING: %s' % str(e)

    db.clear()

    signals.Connections.clear()


main.add_command(deploy)
main.add_command(undeploy)


if __name__ == '__main__':
    main()
