import ipaddress
import subprocess
import os
import sys
import logging
from pathlib import Path
from socket import gethostname

from joblib import Memory

CONTROLLER_IP = {"exclusive": "200.0.0.1",
                 "nonexclusive": "192.168.1.200",
                 }
CHRONY_IP = {"exclusive": "200.0.0.1",
            "nonexclusive": "192.168.1.14",
             }
USERNAME = "worker"
HOSTS = """
            200.0.0.1 controller
            200.0.1.1 acpu1-1
            200.0.1.2 acpu1-2
            200.0.1.3 acpu1-3
            192.168.1.14 epyc1
        """

CACHE_DIR = "/share/installation/src"
JULIA_MAJOR_VER = "1.11"
JULIA_VER = "1.11.4"
AOCC_VER = "5.0.0_1"
INTEL_COMPILER_VER = "2025.0.1.47"


# キャッシュディレクトリの設定
memory = Memory("/tmp", verbose=0)
""" 
@memory.cacheデコレータ付きで定義された関数は実行時に結果が/tmpに保存される．
どこかでこのスクリプトが失敗したあとでもう一度実行すると，成功した関数はスキップされ，失敗した関数から実行が再開される．
"""

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/cluster_setup.log", encoding="utf-8"),  # 通常のログファイル
        logging.FileHandler("/var/log/cluster_setup.err", encoding="utf-8"),  # エラーログファイル
        logging.StreamHandler(sys.stdout)  # 標準出力
    ]
)

# エラーログのみを /var/log/cluster_setup.err に出力するためのフィルタ
class ErrorFilter(logging.Filter):
    def filter(self, record):
        return record.levelno >= logging.ERROR

# エラーログファイルにフィルタを適用
for handler in logging.root.handlers:
    if isinstance(handler, logging.FileHandler) and handler.baseFilename == "/var/log/cluster_setup.err":
        handler.addFilter(ErrorFilter())


def check_vendor(hostname):
    res = subprocess.check_output("cat /proc/cpuinfo", shell=True).decode().strip()
    for line in res.split("\n"):
        if "model name" in line:
            if "Intel" in line:
                assert hostname[0] == "i"
                return
            elif "AMD" in line:
                assert hostname[0] == "a"
                return
    raise ValueError("cpu vendor not identifiable")


def run_command(command, check=True, username="root"):
    """コマンドを実行し、ログを記録する
    username  == "sudo":
        sudoでrootとしてコマンドを実行
    else:
        usernameとしてコマンドを実行
    """
    # shell=True の場合、コマンドを文字列として直接渡す
    full_command = f"sudo -u {username} bash -c '{command}'"

    try:
        logging.info(f"Executing: {full_command}")
        result = subprocess.run(full_command, shell=True, check=check, text=True, capture_output=True)
        logging.info(result.stdout)  # 標準出力をログに記録
        if result.stderr:
            logging.warning(result.stderr)  # 標準エラー出力を警告としてログに記録
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {command}\n{e.stderr}")  # エラーメッセージをエラーログに記録
        raise  # 例外を再送出して呼び出し元にエラーを伝える


@memory.cache
def configure_network(ip):
    """Netplan に固定 IP 設定を追加"""
    netplan_config = f"""
    network:
        version: 2
        ethernets:
            eth0:
                match:
                    name: "enp*"
                addresses:
                - "{ip}/16"
                nameservers:
                  addresses:
                  - "8.8.8.8"
                  - "8.8.4.4"
                routes:
                - to: "default"
                  via: "200.0.0.1"
    """

    assert type(ip) is str
    netplan_path = "/etc/netplan/99-cluster.yaml"
    # ファイルを書き込み
    with open(netplan_path, "w") as f:
        f.write(netplan_config)
    # 権限を適切に設定
    run_command(f"chmod 600 {netplan_path}")
    run_command("mv /etc/netplan/50-cloud-init.yaml /etc/netplan/50-cloud-init.yaml.backup")
    logging.info(f"Cluster setup completed successfully. ip address to be changed to {ip}")
    run_command("netplan apply")


@memory.cache
def configure_hostname(hostname):
    run_command(f"hostname {hostname}")


@memory.cache
def configure_chrony(node_mode):
    """時計同期の設定"""
    run_command("apt install -y chrony")

    chrony_conf = "/etc/chrony/chrony.conf"
    with open(chrony_conf, "r") as f:
        lines = f.readlines()
    
    # server 設定の削除
    lines = [line for line in lines if not line.startswith("server")]

    # クラスタ専属ノードの場合
    chrony_server_ip = CHRONY_IP[node_mode]
    lines.append(f"server {chrony_server_ip} iburst trust\n")
    with open(chrony_conf, "w") as f:
        f.writelines(lines)
    run_command("systemctl restart chrony")


@memory.cache
def setup_nfs(node_mode):
    """NFS クライアントの設定"""
    run_command("apt install -y nfs-common")
    
    # マウント先の作成
    for mount_point in ["/archive", "/share"]:
        if not os.path.exists(mount_point):
            run_command(f"mkdir -p {mount_point}")
            run_command(f"chmod 777 -R {mount_point}")
            run_command(f"chown -R nobody:nogroup {mount_point}")

    # /etc/fstab にマウント設定を追加
    controller_ip = CONTROLLER_IP[node_mode]
    fstab_entry = f"""
        {controller_ip}:/archive /archive nfs defaults 0 0
        {controller_ip}:/share /share nfs defaults 0 0    
        """
    with open("/etc/fstab", "r") as f:
        if fstab_entry not in f.read():
            with open("/etc/fstab", "a") as f_append:
                f_append.write(fstab_entry)
    run_command("mount -a")


@memory.cache
def install_common_packages():
    """一般的なソフトウェアのインストール"""
    run_command("apt update")
    run_command("apt install -y nano ca-certificates curl gnupg software-properties-common")


@memory.cache
def install_apptainer():
    """Apptainer のインストール"""
    run_command("add-apt-repository -y ppa:apptainer/ppa")
    run_command("apt update && apt install -y apptainer")


@memory.cache
def install_docker():
    """Docker のインストール
    rootlessのほうがいいか？
    """
    run_command("install -m 0755 -d /etc/apt/keyrings")
    run_command("curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc")
    run_command("chmod a+r /etc/apt/keyrings/docker.asc")
    
    # なんかうまく動かないのでpythonで書いた
    # repo_cmd = """echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
    # https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    # tee /etc/apt/sources.list.d/docker.list > /dev/null"""
    # run_command(repo_cmd)
    arch = subprocess.check_output(["dpkg", "--print-architecture"], text=True).strip()
    ubuntu_codename = subprocess.check_output(
        ". /etc/os-release && echo ${UBUNTU_CODENAME:-$VERSION_CODENAME}", 
        shell=True, text=True
    ).strip()
    repo_entry = f"deb [arch={arch} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu {ubuntu_codename} stable"
    with open("/etc/apt/sources.list.d/docker.list", "a+") as f:
        f.write("\n"+repo_entry)

    run_command("apt update && apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin")
    run_command("groupadd -f docker")
    run_command("usermod -aG docker worker")


@memory.cache
def install_julia():
    """プログラミング言語のインストール"""
    # Julia
    if not os.path.exists(Path(CACHE_DIR) / f"julia-{JULIA_VER}-linux-x86_64.tar.gz"):
        run_command(f"wget https://julialang-s3.julialang.org/bin/linux/x64/{JULIA_MAJOR_VER}/julia-{JULIA_VER}-linux-x86_64.tar.gz", username="worker")
        run_command(f"mv julia-{JULIA_VER}-linux-x86_64.tar.gz {CACHE_DIR}", username="worker")
    run_command(f"tar zxvf {CACHE_DIR}/julia-{JULIA_VER}-linux-x86_64.tar.gz", username="worker")
    run_command(f"mkdir -p /opt/julia")
    run_command(f"mv julia-{JULIA_VER} /opt/julia")
    run_command(f"""echo "export PATH=/opt/julia/julia-{JULIA_VER}/bin:$PATH" | tee -a /etc/profile.d/julia{JULIA_VER}.sh""")
    run_command(f"chmod +x /etc/profile.d/julia{JULIA_VER}.sh")


@memory.cache
def install_python():
    # Python（rye）
    run_command("""curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR="/usr/local/bin" sh""")

@memory.cache
def install_rust():
    # Rust
    run_command("apt install -y cargo")


@memory.cache
def install_c():
   # C, Fortran
    run_command("apt install -y gcc gfortran build-essential")


@memory.cache
def install_cpu_specific_compilers():
    hostname = gethostname()
    cpu_prefix = hostname[0]
    if cpu_prefix == "a":
        run_command("apt install -y libncurses5-dev")
        run_command("dpkg -i "+ str(Path(CACHE_DIR) / f"aocc-compiler-{AOCC_VER}_amd64.deb"))
        with open("/etc/profile.d/aocc.sh", "w") as f:
            f.write("""
#!/bin/bash
if [ -f /opt/AMD/setenv_AOCC.sh ]; then
    source /opt/AMD/setenv_AOCC.sh
fi
                    """)
        run_command("chmod +x /etc/profile.d/aocc.sh")


    elif cpu_prefix == "i":
        run_command("sh " + str(Path(CACHE_DIR) / f"intel-oneapi-hpc-toolkit-{INTEL_COMPILER_VER}_offline.sh") + "-a --silent --cli --eula accept")


@memory.cache
def check_compiler_version():
    assert os.path.exists(Path(CACHE_DIR) / f"aocc-compiler-{AOCC_VER}_amd64.deb"), f"download aocc-compiler-{AOCC_VER}_amd64.deb to {CACHE_DIR}"
    assert os.path.exists(Path(CACHE_DIR) / f"intel-oneapi-hpc-toolkit-{INTEL_COMPILER_VER}_offline.sh"), f"download intel-oneapi-hpc-toolkit-{INTEL_COMPILER_VER}_offline.sh to {CACHE_DIR}"


@memory.cache
def config_slurm():
    assert (Path(CACHE_DIR) / "slurm.key").exists(), f"slurm.key does not exist in {CACHE_DIR}"
    run_command("apt install -y slurm-wlm")
    run_command("mkdir -p /var/log/slurm && chown -R slurm:slurm /var/log/slurm")
    run_command("mkdir -p /var/spool/slurmctld && chown -R slurm:slurm /var/spool/slurmctld")
    run_command(f"cp {str(Path(CACHE_DIR) / "slurm.key")} /etc/slurm/")
    run_command("chmod 600 /etc/slurm/slurm.key")
    run_command("chown slurm:slurm /etc/slurm/slurm.key")
    with open("/etc/default/slurmd", "a") as f:
        f.write('''\nSLURMD_OPTIONS="--conf-server controller"''')
    run_command("systemctl restart slurmd")


@memory.cache
def update_hostname(hostname):
    run_command(f"hostnamectl set-hostname {hostname}")


@memory.cache
def update_hosts():
    with open("/etc/hosts", "a") as f:
        f.write(HOSTS)

def main(node_mode, hostname, ip):
    """メイン処理"""
    logging.info("Starting cluster setup script...")
    # check_vendor(hostname) virtualboxだとホストのcpuと同じcpuになるのでスキップ

    if node_mode != "controller":
        configure_chrony(node_mode)
        setup_nfs(node_mode)
    configure_network(ip)
    install_common_packages()
    install_apptainer()
    install_docker()
    install_julia()
    install_python()
    install_rust()
    install_c()
    update_hostname(hostname)
    check_compiler_version()
    install_cpu_specific_compilers()
    update_hosts()
    config_slurm()


if __name__ == "__main__":
    import sys
    args = sys.argv
    assert len(args) == 4
    _, node_mode, hostname, ip = args
    assert node_mode in ("controller", "exclusive", "nonexclusive")
    _ = ipaddress.ip_address(ip) # 真正なipであることを確認
    main(node_mode, hostname, ip)
