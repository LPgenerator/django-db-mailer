# -*- mode: ruby -*-

# Options {{{
#
APP_VM_NAME = "dbmail"
APP_MEMORY = "1024"
APP_CPUS = "2"
#
# }}}

# Vagrant 2.0.x {{{
#
Vagrant.configure("2") do |config|

    config.vm.box = "ubuntu/trusty64"
    config.vm.post_up_message = "Box URL is http://127.0.0.1:8000/admin/"

    config.vm.synced_folder "./demo/", "/mailer", id: "vagrant-root"

    config.vm.provision :shell, :path => "demo/.vagrant_bootstrap.sh"
    config.ssh.shell = "bash -c 'BASH_ENV=/etc/profile exec bash'"

    # Set hostname
    config.vm.hostname = APP_VM_NAME

    # Configure network
    config.vm.network :forwarded_port, guest: 8000, host: 8000

    # SSH forward
    config.ssh.forward_agent = true

    # Configure VirtualBox
    config.vm.provider :virtualbox do |vb|
        vb.gui = false
        vb.name = APP_VM_NAME
        vb.customize ["modifyvm", :id, "--memory", APP_MEMORY]
        vb.customize ["modifyvm", :id, "--name", APP_VM_NAME]
        vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
        vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
        vb.customize ["modifyvm", :id, "--ioapic", "on"]
        vb.customize ["modifyvm", :id, "--cpus", APP_CPUS]
    end

end
#
# }}}
