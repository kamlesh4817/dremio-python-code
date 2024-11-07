{
    "id": "/subscriptions/73d6bf3b-48e3-4809-9e31-e0807af07cff/resourcegroups/bagpipe-rg/providers/Microsoft.ContainerService/managedClusters/bagpipe-aks",
    "location": "germanywestcentral",
    "name": "bagpipe-aks",
    "tags": {
        "ps-owner": "max.margalith"
    },
    "type": "Microsoft.ContainerService/ManagedClusters",
    "properties": {
        "provisioningState": "Succeeded",
        "powerState": {
            "code": "Running"
        },
        "kubernetesVersion": "1.30.4",
        "currentKubernetesVersion": "1.30.4",
        "dnsPrefix": "bagpipe-aks-dns",
        "fqdn": "bagpipe-aks-dns-gcyswq4t.hcp.germanywestcentral.azmk8s.io",
        "azurePortalFQDN": "bagpipe-aks-dns-gcyswq4t.portal.hcp.germanywestcentral.azmk8s.io",
        "agentPoolProfiles": [
            {
                "name": "agentpool",
                "count": 1,
                "vmSize": "Standard_D8ds_v5",
                "osDiskSizeGB": 128,
                "osDiskType": "Ephemeral",
                "kubeletDiskType": "OS",
                "maxPods": 110,
                "type": "VirtualMachineScaleSets",
                "availabilityZones": [
                    "1",
                    "2",
                    "3"
                ],
                "maxCount": 5,
                "minCount": 1,
                "enableAutoScaling": true,
                "provisioningState": "Succeeded",
                "powerState": {
                    "code": "Running"
                },
                "orchestratorVersion": "1.30.4",
                "currentOrchestratorVersion": "1.30.4",
                "enableNodePublicIP": false,
                "tags": {
                    "ps-owner": "max.margalith"
                },
                "nodeTaints": [
                    "CriticalAddonsOnly=true:NoSchedule"
                ],
                "mode": "System",
                "osType": "Linux",
                "osSKU": "Ubuntu",
                "nodeImageVersion": "AKSUbuntu-2204gen2containerd-202409.23.0",
                "upgradeSettings": {
                    "maxSurge": "10%"
                },
                "enableFIPS": false
            },
            {
                "name": "nessiepool",
                "count": 1,
                "vmSize": "Standard_D4s_v3",
                "osDiskSizeGB": 128,
                "osDiskType": "Managed",
                "kubeletDiskType": "OS",
                "maxPods": 30,
                "type": "VirtualMachineScaleSets",
                "availabilityZones": [
                    "1",
                    "2",
                    "3"
                ],
                "enableAutoScaling": false,
                "scaleDownMode": "Delete",
                "provisioningState": "Succeeded",
                "powerState": {
                    "code": "Running"
                },
                "orchestratorVersion": "1.30.4",
                "currentOrchestratorVersion": "1.30.4",
                "enableNodePublicIP": false,
                "tags": {
                    "ps-owner": "max.margalith"
                },
                "mode": "User",
                "osType": "Linux",
                "osSKU": "Ubuntu",
                "nodeImageVersion": "AKSUbuntu-2204gen2containerd-202409.23.0",
                "upgradeSettings": {},
                "enableFIPS": false
            },
            {
                "name": "infrapool",
                "count": 1,
                "vmSize": "Standard_D4s_v3",
                "osDiskSizeGB": 128,
                "osDiskType": "Managed",
                "kubeletDiskType": "OS",
                "maxPods": 30,
                "type": "VirtualMachineScaleSets",
                "availabilityZones": [
                    "1"
                ],
                "enableAutoScaling": false,
                "scaleDownMode": "Delete",
                "provisioningState": "Succeeded",
                "powerState": {
                    "code": "Running"
                },
                "orchestratorVersion": "1.30.4",
                "currentOrchestratorVersion": "1.30.4",
                "enableNodePublicIP": false,
                "tags": {
                    "ps-owner": "max.margalith"
                },
                "mode": "User",
                "osType": "Linux",
                "osSKU": "Ubuntu",
                "nodeImageVersion": "AKSUbuntu-2204gen2containerd-202409.23.0",
                "upgradeSettings": {},
                "enableFIPS": false
            },
            {
                "name": "dremiopool",
                "count": 2,
                "vmSize": "Standard_D8ds_v4",
                "osDiskSizeGB": 128,
                "osDiskType": "Ephemeral",
                "kubeletDiskType": "OS",
                "maxPods": 30,
                "type": "VirtualMachineScaleSets",
                "availabilityZones": [
                    "1"
                ],
                "enableAutoScaling": false,
                "scaleDownMode": "Delete",
                "provisioningState": "Succeeded",
                "powerState": {
                    "code": "Running"
                },
                "orchestratorVersion": "1.30.4",
                "currentOrchestratorVersion": "1.30.4",
                "enableNodePublicIP": false,
                "tags": {
                    "ps-owner": "max.margalith"
                },
                "mode": "User",
                "osType": "Linux",
                "osSKU": "Ubuntu",
                "nodeImageVersion": "AKSUbuntu-2204gen2containerd-202409.23.0",
                "upgradeSettings": {},
                "enableFIPS": false
            }
        ],
        "windowsProfile": {
            "adminUsername": "azureuser",
            "enableCSIProxy": true
        },
        "servicePrincipalProfile": {
            "clientId": "msi"
        },
        "addonProfiles": {
            "azureKeyvaultSecretsProvider": {
                "enabled": true,
                "config": {
                    "enableSecretRotation": "true"
                },
                "identity": {
                    "resourceId": "/subscriptions/73d6bf3b-48e3-4809-9e31-e0807af07cff/resourcegroups/MC_bagpipe-rg_bagpipe-aks_germanywestcentral/providers/Microsoft.ManagedIdentity/userAssignedIdentities/azurekeyvaultsecretsprovider-bagpipe-aks",
                    "clientId": "0b9887de-42aa-48e5-900e-e818489007d8",
                    "objectId": "16e294bc-ed3b-4a5f-b4f9-8bbb4d668712"
                }
            },
            "azurepolicy": {
                "enabled": true,
                "config": null,
                "identity": {
                    "resourceId": "/subscriptions/73d6bf3b-48e3-4809-9e31-e0807af07cff/resourcegroups/MC_bagpipe-rg_bagpipe-aks_germanywestcentral/providers/Microsoft.ManagedIdentity/userAssignedIdentities/azurepolicy-bagpipe-aks",
                    "clientId": "09bb5678-6d91-444a-8c98-34a4f7b65c42",
                    "objectId": "f488199c-6338-4e01-b5a0-105adb0a648d"
                }
            }
        },
        "nodeResourceGroup": "MC_bagpipe-rg_bagpipe-aks_germanywestcentral",
        "enableRBAC": true,
        "supportPlan": "KubernetesOfficial",
        "networkProfile": {
            "networkPlugin": "azure",
            "networkPluginMode": "overlay",
            "networkPolicy": "azure",
            "networkDataplane": "azure",
            "loadBalancerSku": "Standard",
            "loadBalancerProfile": {
                "managedOutboundIPs": {
                    "count": 1
                },
                "effectiveOutboundIPs": [
                    {
                        "id": "/subscriptions/73d6bf3b-48e3-4809-9e31-e0807af07cff/resourceGroups/MC_bagpipe-rg_bagpipe-aks_germanywestcentral/providers/Microsoft.Network/publicIPAddresses/376cf659-8b93-4d68-bafb-f58169bc1b30"
                    }
                ],
                "backendPoolType": "nodeIPConfiguration"
            },
            "podCidr": "10.244.0.0/16",
            "serviceCidr": "10.0.0.0/16",
            "dnsServiceIP": "10.0.0.10",
            "outboundType": "loadBalancer",
            "podCidrs": [
                "10.244.0.0/16"
            ],
            "serviceCidrs": [
                "10.0.0.0/16"
            ],
            "ipFamilies": [
                "IPv4"
            ]
        },
        "maxAgentPools": 100,
        "apiServerAccessProfile": {
            "authorizedIPRanges": [
                "91.21.26.214/32",
                "172.97.219.23/32",
                "72.136.110.102/32",
                "216.58.25.200/32",
                "73.197.185.87/32"
            ]
        },
        "identityProfile": {
            "kubeletidentity": {
                "resourceId": "/subscriptions/73d6bf3b-48e3-4809-9e31-e0807af07cff/resourcegroups/MC_bagpipe-rg_bagpipe-aks_germanywestcentral/providers/Microsoft.ManagedIdentity/userAssignedIdentities/bagpipe-aks-agentpool",
                "clientId": "8e23f38a-7745-4ecf-a59e-c4378823ee5a",
                "objectId": "a871c225-decb-4865-8692-8fa0f1271930"
            }
        },
        "autoScalerProfile": {
            "balance-similar-node-groups": "false",
            "expander": "random",
            "max-empty-bulk-delete": "10",
            "max-graceful-termination-sec": "600",
            "max-node-provision-time": "15m",
            "max-total-unready-percentage": "45",
            "new-pod-scale-up-delay": "0s",
            "ok-total-unready-count": "3",
            "scale-down-delay-after-add": "10m",
            "scale-down-delay-after-delete": "10s",
            "scale-down-delay-after-failure": "3m",
            "scale-down-unneeded-time": "10m",
            "scale-down-unready-time": "20m",
            "scale-down-utilization-threshold": "0.5",
            "scan-interval": "10s",
            "skip-nodes-with-local-storage": "false",
            "skip-nodes-with-system-pods": "true"
        },
        "autoUpgradeProfile": {
            "upgradeChannel": "patch",
            "nodeOSUpgradeChannel": "NodeImage"
        },
        "disableLocalAccounts": false,
        "securityProfile": {},
        "storageProfile": {
            "diskCSIDriver": {
                "enabled": true
            },
            "fileCSIDriver": {
                "enabled": true
            },
            "snapshotController": {
                "enabled": true
            }
        },
        "oidcIssuerProfile": {
            "enabled": true,
            "issuerURL": "https://germanywestcentral.oic.prod-aks.azure.com/3e334762-b0c6-4c36-9faf-93800f0d6c71/d2116507-a0de-4ca3-9c5d-158b77db3705/"
        },
        "workloadAutoScalerProfile": {},
        "resourceUID": "66cd7c2e9eeeed0001277582"
    },
    "identity": {
        "type": "SystemAssigned",
        "principalId": "4f501698-611b-4dfc-87be-2ed4e10d671e",
        "tenantId": "3e334762-b0c6-4c36-9faf-93800f0d6c71"
    },
    "sku": {
        "name": "Base",
        "tier": "Standard"
    }
}