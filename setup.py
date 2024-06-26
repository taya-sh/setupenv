#!/usr/bin/env python3
#     ____ _                   _     _         _   _ _____ _____ 
#    / ___| |__   ___  ___ ___| |__ (_) __ _  | \ | | ____|_   _|
#   | |   | '_ \ / _ \/ __/ __| '_ \| |/ _` | |  \| |  _|   | |  
#   | |___| | | |  __/ (_| (__| | | | | (_| |_| |\  | |___  | |  
#    \____|_| |_|\___|\___\___|_| |_|_|\__,_(_)_| \_|_____| |_|  
#                                                                
# Script para setup inicial de novos servidores Ubuntu


import os
import sys
import subprocess
import platform


# Verificar se o usuário é root
if os.geteuid() != 0:
    print("Este script precisa ser executado como root.")
    sys.exit(1)

bash_shebang = '#!/bin/bash'
rc_local_path = '/etc/rc.local'
required_line = '/etc/init.d/procps restart'
exit_line = 'exit 0'

banner_content = """#!/bin/bash
clear

# Definir cores e formatações
yellow_bold="\\033[1;33m"
red_bold="\\033[1;31m"
red_bold_blink="\\033[1;5;31m"
bold="\\033[1m"
reset="\\033[0m"

/usr/bin/neofetch



# Mensagem sobre acesso não autorizado
echo -e "${red_bold}      A V I S O   D E   S E G U R A N Ç A!!!${reset} "
echo " "
echo -e "${bold}O acesso não autorizado a este sistema é proibido.${reset}"
echo -e "Qualquer atividade não autorizada será ${red_bold}monitorada e registrada${reset} e pode resultar em ${red_bold}processos criminais${reset}."
echo -e "Usuários que tentarem acessar o sistema sem autorização estarão sujeitos a ${bold}penalidades severas${reset} conforme as leis vigentes."

echo " "

# Verificar se o usuário logado é root ou possui privilégios sudoers
if [ "$EUID" -eq 0 ]; then
  echo -e "${red_bold}VOCÊ ESTÁ ACESSANDO COMO USUÁRIO PRIVILEGIADO!${reset}"
  echo -e "${red_bold_blink}\"Com grandes poderes vêm grandes responsabilidades! Não se esqueça!\"${reset}"
  echo " "

  # Verificar quantos pacotes precisam ser atualizados
  updates_count=$(apt list --upgradable 2>/dev/null | grep -c upgradable)

  # Verificar quantos pacotes de segurança precisam ser atualizados
  security_updates_count=$(apt list --upgradable 2>/dev/null | grep -c "security")

  # Exibir a quantidade de pacotes a serem atualizados, se maior que zero
  if [ $updates_count -gt 0 ]; then
    echo -e "${red_bold}Pacotes que precisam ser atualizados: ${updates_count}${reset}"
  fi

  # Exibir a quantidade de pacotes de segurança a serem atualizados, se maior que zero
  if [ $security_updates_count -gt 0 ]; then
    echo -e "${red_bold}Pacotes de segurança que precisam ser atualizados: ${security_updates_count}${reset}"
  fi
else
  echo " "
fi
echo " "
"""

file_path = "/etc/profile.d/00-banner.sh"

def disable_ipv6():
    try:
        # Abrir o arquivo de configuração do sysctl em modo de escrita
        with open('/etc/sysctl.conf', 'a') as sysctl_file:
            # Adicionar a configuração para desativar o IPv6
            sysctl_file.write('net.ipv6.conf.all.disable_ipv6 = 1\n')
            sysctl_file.write('net.ipv6.conf.default.disable_ipv6 = 1\n')
            sysctl_file.write('net.ipv6.conf.lo.disable_ipv6 = 1\n')    
        # Recarregar as configurações do sysctl
        subprocess.run(['sudo', 'sysctl', '-p'], stdout=subprocess.DEVNULL)
        
        status("IPv6 desativado com sucesso!",0)
    except Exception as e:
        status(f"Erro ao desativar o IPv6: {e}",1)

def checkversion():
    if sys.version_info >= (3, 10):
        status("A versão do Python é igual ou superior à 3.10",0)
    else:
        status("A versão do Python é inferior à 3.10",1)
        sys.exit(1)

def status(mensagem, codigo):
    if codigo == 0:
        status = "\033[1;32m[OK]\033[0m"
    elif codigo == 1:
        status = "\033[1;31m[FALHA]\033[0m"
    else:
        status = "[Código inválido]"
    print(f"{mensagem.ljust(80-len(status))}{status}")

def install_packages():
    packages = ['ufw','neofetch','net-tools','vim','python3-pip','python-is-python3','rsyslog','screen','auditd','figlet','inetutils-traceroute','whois']
    try:
        subprocess.run(['sudo', 'apt', 'update', '-y'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        status("Rodando apt update!",0)
    except subprocess.CalledProcessError as e:
        status("Erro ao rodar apt update",1)
    try:
        subprocess.run(['sudo', 'apt', 'dist-upgrade', '-y'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        status("Atualização de pacotes",0)
    except subprocess.CalledProcessError as e:
        status("Erro atualizando os pacotes",1)

    try:
        for package in packages:
            subprocess.run(['sudo', 'apt', 'install', '-y', package], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            status(f"Pacote {package} com sucesso!",0)
    except subprocess.CalledProcessError as e:
        status(f"Erro ao instalar {package}",1)

def enable_auditd():
    try:
        subprocess.run(["sudo", "systemctl", "enable", "auditd"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        status("Habilitado o serviço auditd.",0)
    except:
        status("Erro habilitando o serviço auditd.",1)

def start_auditd():
    try:
        subprocess.run(["sudo", "systemctl", "start", "auditd"], stdout=subprocess.DEVNULL)
        status("Serviço auditd iniciado.",0)
    except:
        status("Erro iniciando o serviço auditd!",1)

def configure_audit_rules():
    audit_rules = [
        "-a always,exit -F arch=b64 -S execve",
        "-a always,exit -F arch=b32 -S execve",
        "-w /etc/passwd -p wa -k identity",
        "-w /etc/group -p wa -k identity",
        "-w /etc/shadow -p wa -k identity",
        "-w /etc/sudoers -p wa -k sudoers_changes",
        "-w /var/log/auth.log -p wa -k authentication_events"
        # Adicione outras regras conforme necessário
    ]
    with open("/etc/audit/rules.d/infra.rules", "a") as f:
        for rule in audit_rules:
            f.write(rule + "\n")
    try:
        subprocess.run(["sudo", "auditctl", "-l"], stdout=subprocess.DEVNULL)
        status("Regras de auditoria validadas",0)
    except:
        status("Erros durante validação de regras de uditoria!",1)
    try:
        subprocess.run(["sudo", "systemctl", "restart", "auditd"], stdout=subprocess.DEVNULL)
        status("Serviço auditd reiniciado.",0)
    except:
        status("Erro na reinicialização do serviço auditd!",1)

def check_and_update_rc_local():
    # Verificar se o arquivo rc.local existe
    if not os.path.exists(rc_local_path):
        # Criar o arquivo com o conteúdo necessário
        with open(rc_local_path, 'w') as file:
            file.write(f'{bash_shebang}\n')
            file.write('# /etc/rc.local\n')
            file.write('# Load kernel variables from /etc/sysctl.d\n')
            file.write(f'{required_line}\n')
            file.write(f'{exit_line}\n')
        # Tornar o arquivo executável
        os.chmod(rc_local_path, 0o755)
        status(f'Arquivo {rc_local_path} criado com sucesso.',0)
    else:
        # Ler o conteúdo atual do arquivo
        with open(rc_local_path, 'r') as file:
            lines = file.readlines()

        # Remover novas linhas e espaços extras das linhas
        lines = [line.strip() for line in lines]

        # Garantir que a primeira linha é o shebang correto
        if not lines or lines[0] != bash_shebang:
            lines.insert(0, bash_shebang)
            status(f'Shebang "{bash_shebang}" adicionado ao início do arquivo.',0)

        # Verificar se a linha necessária está presente
        if required_line not in lines:
            # Inserir a linha necessária antes do exit 0
            new_lines = []
            exit_found = False
            for line in lines:
                if line == exit_line:
                    new_lines.append(required_line)
                    exit_found = True
                new_lines.append(line)
            if not exit_found:
                new_lines.append(required_line)
            lines = new_lines
            status(f'Linha "{required_line}" adicionada ao arquivo.',0)
        else:
            status(f'A linha "{required_line}" já está presente no arquivo.',0)

        # Verificar se a linha 'exit 0' existe
        if exit_line not in lines:
            # Adicionar 'exit 0' como última linha se não existir
            lines.append(exit_line)
            status(f'Linha "{exit_line}" adicionada ao final do arquivo.',0)
        else:
            status(f'A linha "{exit_line}" já está presente no arquivo.',0)

        # Escrever as linhas atualizadas de volta para o arquivo
        with open(rc_local_path, 'w') as file:
            for line in lines:
                file.write(line + '\n')

    try:
        subprocess.run(["sudo", "chmod", "755", "/etc/rc.local"], stdout=subprocess.DEVNULL)
        status("Executando chmod para execução /etc/rc.local.",0)
    except:
        status("Erro executando chmod /etc/rc.local",1)

def configure_ufw_for_ssh():
    try:
        # Permitir o acesso à porta 22 (SSH)
        subprocess.run(['sudo', 'ufw', 'allow', '22'], check=True, stdout=subprocess.DEVNULL)
        status("Porta 22 liberada com sucesso.",0)
        
        # Habilitar o UFW
        subprocess.run(['sudo', 'ufw', '--force', 'enable'], check=True, stdout=subprocess.DEVNULL)
        status("UFW habilitado com sucesso.",0)
        
    except subprocess.CalledProcessError as e:
        status(f"Ocorreu um erro ao configurar o UFW!!!",1)

if __name__ == "__main__":
    checkversion()
    disable_ipv6()
    check_and_update_rc_local()
    try:
        with open(file_path, "w") as file:
            file.write(banner_content)
        status(f"Arquivo {file_path} criado com sucesso.",0)
    except PermissionError:
        status(f"Você não tem permissões para escrever em {file_path}. Execute o script como superusuário (root) ou com permissões de escrita adequadas.",1)
    install_packages()
    configure_ufw_for_ssh()
    enable_auditd()
    start_auditd()
    configure_audit_rules()
