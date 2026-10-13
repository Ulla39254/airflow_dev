import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def hana_connection(hana_conn_id: str = "hana_default", ssh_conn_id: str = "hana_ssh"):
    """
    Open an SSH tunnel to the HANA host and yield an hdbcli connection through it.

    - `ssh_conn_id`: SSH connection to the HANA server (host, login, private key).
    - `hana_conn_id`: HANA DB credentials. Host/port are as seen *from the SSH server*
      (normally localhost:30015); any extras (e.g. databaseName, encrypt) are passed to hdbcli.

    The tunnel binds to 127.0.0.1 on a random free port and is closed when the block exits.
    """
    # Import lazily so DAG parsing doesn't pay the import cost
    from airflow.providers.ssh.hooks.ssh import SSHHook
    from airflow.sdk import BaseHook
    from hdbcli import dbapi

    hana = BaseHook.get_connection(hana_conn_id)
    tunnel = SSHHook(ssh_conn_id=ssh_conn_id).get_tunnel(
        remote_port=hana.port or 30015,
        remote_host=hana.host or "localhost",
    )

    with tunnel:
        logger.info("SSH tunnel open: 127.0.0.1:%s -> %s:%s", tunnel.local_bind_port, hana.host, hana.port)
        conn = dbapi.connect(
            address="127.0.0.1",
            port=tunnel.local_bind_port,
            user=hana.login,
            password=hana.password,
            **hana.extra_dejson,
        )
        try:
            yield conn
        finally:
            conn.close()
