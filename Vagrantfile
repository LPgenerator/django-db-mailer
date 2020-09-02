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

    config.vm.box = "ubuntu/xenial64"
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

    # VirtualBox configuration
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

    # LXC configuration
    config.vm.provider :lxc do |lxc, override|
        override.vm.box = "fgrehm/xenial64-lxc"
    end

    if Vagrant.has_plugin?("vagrant-cachier")
        config.cache.scope = :box
        config.vm.network :private_network, ip: "44.44.44.45"

        config.cache.synced_folder_opts = {
            type: :nfs,
            mount_options: ['rw', 'vers=3', 'tcp', 'nolock']
        }
    end
end
#
# }}}
