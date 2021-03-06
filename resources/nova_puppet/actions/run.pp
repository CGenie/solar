$resource = hiera($::resource_name)

$db_user = $resource['input']['db_user']['value']
$db_password = $resource['input']['db_password']['value']
$db_name = $resource['input']['db_name']['value']
$db_host = $resource['input']['db_host']['value']
$glance_api_servers_host = $resource['input']['glance_api_servers_host']['value']
$glance_api_servers_port = $resource['input']['glance_api_servers_port']['value']

$ensure_package            = $resource['input']['ensure_package']['value']
$database_connection       = $resource['input']['database_connection']['value']
$slave_connection          = $resource['input']['slave_connection']['value']
$database_idle_timeout     = $resource['input']['database_idle_timeout']['value']
$rpc_backend               = $resource['input']['rpc_backend']['value']
$image_service             = $resource['input']['image_service']['value']
$glance_api_servers        = $resource['input']['glance_api_servers']['value']
$memcached_servers         = $resource['input']['memcached_servers']['value']
$rabbit_host               = $resource['input']['rabbit_host']['value']
$rabbit_hosts              = $resource['input']['rabbit_hosts']['value']
$rabbit_password           = $resource['input']['rabbit_password']['value']
$rabbit_port               = $resource['input']['rabbit_port']['value']
$rabbit_userid             = $resource['input']['rabbit_userid']['value']
$rabbit_virtual_host       = $resource['input']['rabbit_virtual_host']['value']
$rabbit_use_ssl            = $resource['input']['rabbit_use_ssl']['value']
$rabbit_ha_queues          = $resource['input']['rabbit_ha_queues']['value']
$kombu_ssl_ca_certs        = $resource['input']['kombu_ssl_ca_certs']['value']
$kombu_ssl_certfile        = $resource['input']['kombu_ssl_certfile']['value']
$kombu_ssl_keyfile         = $resource['input']['kombu_ssl_keyfile']['value']
$kombu_ssl_version         = $resource['input']['kombu_ssl_version']['value']
$amqp_durable_queues       = $resource['input']['amqp_durable_queues']['value']
$qpid_hostname             = $resource['input']['qpid_hostname']['value']
$qpid_port                 = $resource['input']['qpid_port']['value']
$qpid_username             = $resource['input']['qpid_username']['value']
$qpid_password             = $resource['input']['qpid_password']['value']
$qpid_sasl_mechanisms      = $resource['input']['qpid_sasl_mechanisms']['value']
$qpid_heartbeat            = $resource['input']['qpid_heartbeat']['value']
$qpid_protocol             = $resource['input']['qpid_protocol']['value']
$qpid_tcp_nodelay          = $resource['input']['qpid_tcp_nodelay']['value']
$auth_strategy             = $resource['input']['auth_strategy']['value']
$service_down_time         = $resource['input']['service_down_time']['value']
$log_dir                   = $resource['input']['log_dir']['value']
$state_path                = $resource['input']['state_path']['value']
$lock_path                 = $resource['input']['lock_path']['value']
$verbose                   = $resource['input']['verbose']['value']
$debug                     = $resource['input']['debug']['value']
$periodic_interval         = $resource['input']['periodic_interval']['value']
$report_interval           = $resource['input']['report_interval']['value']
$rootwrap_config           = $resource['input']['rootwrap_config']['value']
$use_ssl                   = $resource['input']['use_ssl']['value']
$enabled_ssl_apis          = $resource['input']['enabled_ssl_apis']['value']
$ca_file                   = $resource['input']['ca_file']['value']
$cert_file                 = $resource['input']['cert_file']['value']
$key_file                  = $resource['input']['key_file']['value']
$nova_user_id              = $resource['input']['nova_user_id']['value']
$nova_group_id             = $resource['input']['nova_group_id']['value']
$nova_public_key           = $resource['input']['nova_public_key']['value']
$nova_private_key          = $resource['input']['nova_private_key']['value']
$nova_shell                = $resource['input']['nova_shell']['value']
$monitoring_notifications  = $resource['input']['monitoring_notifications']['value']
$use_syslog                = $resource['input']['use_syslog']['value']
$log_facility              = $resource['input']['log_facility']['value']
$install_utilities         = $resource['input']['install_utilities']['value']
$notification_driver       = $resource['input']['notification_driver']['value']
$notification_topics       = $resource['input']['notification_topics']['value']
$notify_api_faults         = $resource['input']['notify_api_faults']['value']
$notify_on_state_change    = $resource['input']['notify_on_state_change']['value']
$mysql_module              = $resource['input']['mysql_module']['value']
$nova_cluster_id           = $resource['input']['nova_cluster_id']['value']
$sql_connection            = $resource['input']['sql_connection']['value']
$sql_idle_timeout          = $resource['input']['sql_idle_timeout']['value']
$logdir                    = $resource['input']['logdir']['value']
$os_region_name            = $resource['input']['os_region_name']['value']

class { 'nova':
  database_connection       => "mysql://${db_user}:${db_password}@${db_host}/${db_name}?charset=utf8",
  ensure_package            => $ensure_package,
  slave_connection          => $slave_connection,
  database_idle_timeout     => $database_idle_timeout,
  rpc_backend               => $rpc_backend,
  image_service             => $image_service,
  glance_api_servers        => "${glance_api_servers_host}:${glance_api_servers_port}",
  memcached_servers         => $memcached_servers,
  rabbit_host               => $rabbit_host,
  rabbit_hosts              => $rabbit_hosts,
  rabbit_password           => $rabbit_password,
  rabbit_port               => $rabbit_port,
  rabbit_userid             => $rabbit_userid,
  rabbit_virtual_host       => $rabbit_virtual_host,
  rabbit_use_ssl            => $rabbit_use_ssl,
  rabbit_ha_queues          => $rabbit_ha_queues,
  kombu_ssl_ca_certs        => $kombu_ssl_ca_certs,
  kombu_ssl_certfile        => $kombu_ssl_certfile,
  kombu_ssl_keyfile         => $kombu_ssl_keyfile,
  kombu_ssl_version         => $kombu_ssl_version,
  amqp_durable_queues       => $amqp_durable_queues,
  qpid_hostname             => $qpid_hostname,
  qpid_port                 => $qpid_port,
  qpid_username             => $qpid_username,
  qpid_password             => $qpid_password,
  qpid_sasl_mechanisms      => $qpid_sasl_mechanisms,
  qpid_heartbeat            => $qpid_heartbeat,
  qpid_protocol             => $qpid_protocol,
  qpid_tcp_nodelay          => $qpid_tcp_nodelay,
  auth_strategy             => $auth_strategy,
  service_down_time         => $service_down_time,
  log_dir                   => $log_dir,
  state_path                => $state_path,
  lock_path                 => $lock_path,
  verbose                   => $verbose,
  debug                     => $debug,
  periodic_interval         => $periodic_interval,
  report_interval           => $report_interval,
  rootwrap_config           => $rootwrap_config,
  use_ssl                   => $use_ssl,
  enabled_ssl_apis          => $enabled_ssl_apis,
  ca_file                   => $ca_file,
  cert_file                 => $cert_file,
  key_file                  => $key_file,
  nova_user_id              => $nova_user_id,
  nova_group_id             => $nova_group_id,
  nova_public_key           => $nova_public_key,
  nova_private_key          => $nova_private_key,
  nova_shell                => $nova_shell,
  monitoring_notifications  => $monitoring_notifications,
  use_syslog                => $use_syslog,
  log_facility              => $log_facility,
  install_utilities         => $install_utilities,
  notification_driver       => $notification_driver,
  notification_topics       => $notification_topics,
  notify_api_faults         => $notify_api_faults,
  notify_on_state_change    => $notify_on_state_change,
  mysql_module              => $mysql_module,
  nova_cluster_id           => $nova_cluster_id,
  sql_idle_timeout          => $sql_idle_timeout,
  logdir                    => $logdir,
  os_region_name            => $os_region_name,
}
