# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

import paramiko
from io import StringIO

# === Connection Parameters ===
host = "your-sftp-host.com"
port = 22
username = "your-username"

# === OpenSSH Private Key ===
private_key_str = """-----BEGIN OPENSSH PRIVATE KEY-----
MKA9n3CYF8dY+j9P713bUoWelyJtFdv8gNpfn8pkzoc...<truncated for brevity>...
-----END OPENSSH PRIVATE KEY-----"""

try:
    # Wrap the private key string into a file-like object
    private_key_file = StringIO(private_key_str)
    pkey = paramiko.RSAKey.from_private_key(private_key_file)

    # Establish transport and connect
    transport = paramiko.Transport((host, port))
    transport.connect(username=username, pkey=pkey)

    # Create SFTP client
    sftp = paramiko.SFTPClient.from_transport(transport)

    print("✅ SFTP connection successful.")
    print("📂 Remote file list:", sftp.listdir("."))

    sftp.close()
    transport.close()

except Exception as e:
    print("❌ SFTP connection failed:", str(e))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
